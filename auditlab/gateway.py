"""Session-scoped, fixed-upstream Mistral gateway; controller telemetry only.

No tokenizer is bundled. Reservation units are request bytes plus an output
allowance, not a claim about billed tokens. Missing provider usage stops a session.
"""
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from contextlib import nullcontext
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .io import fresh, load, write
from .pacing import Pacer

UPSTREAM = "https://api.mistral.ai/v1/chat/completions"
FIELDS = {"model", "messages", "tools", "tool_choice", "parallel_tool_calls",
          "stream", "stream_options", "max_tokens", "temperature", "top_p",
          "random_seed", "stop", "response_format", "safe_prompt", "prompt_mode",
          "prompt_cache_key"}


def validate_config(cfg):
    models = cfg.get("models")
    if (not isinstance(models, list) or len(models) != 2
            or any(not isinstance(m, str) or not m or "latest" in m for m in models)
            or len(set(models)) != 2):
        raise ValueError("Select two distinct non-latest Mistral API model IDs")
    for key in ("max_requests", "max_request_bytes", "max_response_bytes",
                "max_output_tokens", "reservation_units", "observed_token_limit",
                "ttl_seconds", "upstream_timeout_seconds"):
        if type(cfg.get(key)) is not int or cfg[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    if cfg.get("free_only") is not True:
        raise ValueError("Only Free-mode experiments are authorized")
    if 'tokens_per_minute' in cfg:
        if (set(cfg['tokens_per_minute']) != set(models)
                or any(type(v) is not int or v < 1 for v in cfg['tokens_per_minute'].values())
                or cfg.get('minimum_start_interval_seconds', 0) < 3):
            raise ValueError('Invalid shared pacing limits')
    return cfg


def provider_usage(data, content_type):
    """Require structurally valid provider token telemetry; never invent zero."""
    usage = None
    if "text/event-stream" in content_type:
        done = False
        for line in data.decode("utf-8").splitlines():
            if not line.startswith("data:"):
                continue
            value = line[5:].strip()
            if value == "[DONE]":
                done = True
                continue
            if not value:
                continue
            event = json.loads(value)
            if not isinstance(event, dict):
                raise ValueError("Invalid stream event")
            if event.get("usage") is not None:
                usage = event["usage"]
        if not done:
            raise ValueError("Provider stream is incomplete")
    else:
        result = json.loads(data)
        if not isinstance(result, dict):
            raise ValueError("Invalid provider response")
        usage = result.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("Provider usage missing")
    keys = ("prompt_tokens", "completion_tokens", "total_tokens")
    if any(type(usage.get(k)) is not int or usage[k] < 0 for k in keys):
        raise ValueError("Provider usage schema drift")
    if usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]:
        raise ValueError("Provider usage denominator mismatch")
    return {key: usage[key] for key in keys}


class Gateway:
    def __init__(self, cfg, token, api_key, ledger, model, transport=None, clock=time.monotonic, pacing_state=None):
        self.cfg = validate_config(cfg)
        if model not in cfg["models"]:
            raise ValueError("Session model is not allowed")
        if len(token) < 32 or not api_key:
            raise ValueError("Gateway token (at least 32 characters) and provider key required")
        self.token, self.api_key, self.model = token, api_key, model
        self.ledger, self.clock = Path(ledger), clock
        self.deadline = clock() + cfg["ttl_seconds"]
        self.requests = self.reserved = self.observed = 0
        self.stopped = False
        self.transport = transport or self.forward
        self.pacer = (Pacer(pacing_state or os.environ.get('AUDITLAB_PACING_STATE')
                            or self.ledger.parent / 'pacing.json', cfg['tokens_per_minute'],
                            cfg['minimum_start_interval_seconds'])
                      if 'tokens_per_minute' in cfg else None)

    def record(self, value):
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(value) + "\n")

    def forward(self, payload):
        # Ignore environment proxies and prohibit redirects to other destinations.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        request = urllib.request.Request(UPSTREAM, data=payload, method="POST", headers={
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
        })
        with opener.open(request, timeout=self.cfg["upstream_timeout_seconds"]) as response:
            data = response.read(self.cfg["max_response_bytes"] + 1)
            if len(data) > self.cfg["max_response_bytes"]:
                raise ValueError("Provider response exceeds size limit")
            return response.status, response.headers.get("Content-Type", "application/json"), data

    def handle(self, path, authorization, raw):
        def error(status, message):
            return status, "application/json", json.dumps({"error": {"message": message}}).encode()
        if not hmac.compare_digest(authorization, "Bearer " + self.token):
            return error(401, "Invalid session token")
        if path != "/v1/chat/completions":
            return error(403, "Endpoint is not allowed")
        if self.stopped or self.clock() >= self.deadline:
            return error(403, "Session stopped or expired")
        if len(raw) > self.cfg["max_request_bytes"]:
            return error(413, "Request exceeds size limit")
        try:
            body = json.loads(raw)
            if not isinstance(body, dict) or set(body) - FIELDS:
                raise ValueError("Unknown request fields")
            if body.get("model") != self.model:
                raise ValueError("Request model differs from session model")
            if 'prompt_cache_key' in body and (not isinstance(body['prompt_cache_key'], str)
                                               or len(body['prompt_cache_key']) > 64):
                raise ValueError("Invalid prompt cache key")
            messages = body.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError("Messages are required")
            for message in messages:
                if not isinstance(message, dict):
                    raise ValueError("Invalid message")
                content = message.get("content")
                if content is not None and not isinstance(content, str):
                    if not isinstance(content, list) or any(
                        not isinstance(part, dict) or part.get("type") != "text"
                        or not isinstance(part.get("text"), str) for part in content
                    ):
                        raise ValueError("Only text content is supported")
            requested = body.get("max_tokens", self.cfg["max_output_tokens"])
            if type(requested) is not int or requested < 1:
                raise ValueError("Invalid max_tokens")
            if type(body.get("stream", False)) is not bool:
                raise ValueError("Invalid stream flag")
            body["max_tokens"] = min(requested, self.cfg["max_output_tokens"])
            body["temperature"] = 0
            payload = json.dumps(body, ensure_ascii=False).encode()
        except (ValueError, TypeError, UnicodeError) as exc:
            self.record({"status": "rejected_request", "model": self.model,
                "upstream_dispatched": False, "usage": None,
                "reason": str(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError) else "Invalid JSON shape",
                "request_keys": sorted(body) if isinstance(locals().get("body"), dict) else None,
                "request_sha256": hashlib.sha256(raw).hexdigest()})
            return error(400, "Invalid or unsupported completion request")
        reservation = len(payload) + body["max_tokens"] + 4096
        if (self.requests >= self.cfg["max_requests"]
                or self.reserved + reservation > self.cfg["reservation_units"]
                or self.observed >= self.cfg["observed_token_limit"]):
            self.stopped = True
            self.record({'status': 'rejected_budget', 'model': self.model,
                         'upstream_dispatched': False, 'usage': None,
                         'local_status': 429, 'requested_reservation_units': reservation,
                         'reserved_units_total': self.reserved, 'observed_tokens': self.observed,
                         'request_count': self.requests})
            return error(429, "Local experiment budget exhausted")
        # Serialized HTTPServer and pre-dispatch reservations prevent concurrent overruns.
        self.requests += 1
        self.reserved += reservation
        record = {"request_index": self.requests, "model": self.model,
                  "request_sha256": hashlib.sha256(payload).hexdigest(),
                  "request_bytes": len(payload), "reserved_units": reservation,
                  "max_output_tokens": body["max_tokens"], "temperature": 0,
                  "usage": None, "cost_usd": None, "status": "dispatching"}
        # Write before dispatch: an interrupted upstream request remains an unknown attempt.
        self.record(record)
        try:
            slot = (self.pacer.slot(self.model, reservation, max(0, self.deadline - self.clock()))
                    if self.pacer else nullcontext({}))
            with slot as event:
                record['upstream_start_epoch'] = event.get('start', time.time())
                if self.pacer:
                    self.record({**record, 'status': 'upstream_started'})
                status, content_type, data = self.transport(payload)
                record["upstream_status"] = status
                record["response_sha256"] = hashlib.sha256(data).hexdigest()
                if not 200 <= status < 300:
                    raise ValueError("Provider returned an error")
                usage = provider_usage(data, content_type)
                event['usage'] = usage
            record.update(status="completed", usage=usage)
            record['upstream_finished_epoch'] = time.time()
            self.observed += usage["total_tokens"]
            self.record(record)
            return status, content_type, data
        except (OSError, ValueError, TypeError, UnicodeError, urllib.error.URLError) as exc:
            # Do not return/log exception text: provider error text may include secrets.
            self.stopped = True
            record["status"] = "error_usage_unknown"
            record["error_type"] = type(exc).__name__
            if isinstance(exc, urllib.error.HTTPError):
                record["upstream_status"] = exc.code
                retry = exc.headers.get("Retry-After") if exc.headers else None
                record["retry_after"] = (str(retry).replace(self.api_key, '[REDACTED]')
                                         .replace(self.token, '[REDACTED]')[:500] if retry else None)
                record['rate_limit_headers'] = {
                    k: str(v).replace(self.api_key, '[REDACTED]').replace(self.token, '[REDACTED]')[:500]
                    for k, v in (exc.headers.items() if exc.headers else [])
                    if (k.lower() == 'retry-after' or k.lower().startswith(('ratelimit', 'x-ratelimit', 'x-rate-limit')))}
                try:
                    detail = json.loads(exc.read(8192))
                    if isinstance(detail, dict) and isinstance(detail.get('error'), dict):
                        detail = detail['error']
                    if isinstance(detail, dict):
                        record['provider_error'] = {
                            k: str(detail[k]).replace(self.api_key, '[REDACTED]').replace(self.token, '[REDACTED]')[:500]
                            for k in ('message', 'type', 'code', 'detail')
                            if isinstance(detail.get(k), (str, int))}
                except (OSError, ValueError):
                    pass
                finally:
                    exc.close()
            self.record(record)
            return error(502, "Provider error or missing usage; session stopped")


def serve(config, out, model, host="127.0.0.1", port=8080, execute=False, confirm_free_only=False):
    cfg = validate_config(load(config))
    if model not in cfg["models"]:
        raise ValueError("Session model is not allowed")
    out = fresh(out)
    write(out / "gateway.json", {"status": "planned", "config": cfg,
        "upstream": UPSTREAM, "model": model, "host": host, "port": port,
        "free_mode_confirmed": confirm_free_only,
        "note": "Provider limits and billing are account-specific. No tokenization guarantee. Ledger events are per request, not independent agent runs."})
    if not execute:
        return {"status": "planned", "out": str(out)}
    if not confirm_free_only:
        raise ValueError("Confirm Free mode and disabled pay-as-you-go before execution")
    gateway = Gateway(cfg, os.environ.get("AUDITLAB_GATEWAY_TOKEN", ""),
                      os.environ.get("MISTRAL_API_KEY", ""), out / "usage.jsonl", model)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, *args):
            pass

        def do_POST(self):
            self.connection.settimeout(15)
            try:
                length = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                length = -1
            if (not 0 <= length <= cfg["max_request_bytes"]
                    or self.headers.get("Transfer-Encoding")
                    or self.headers.get("Content-Encoding", "identity") != "identity"):
                self.send_error(400)
                return
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    self.send_error(400)
                    return
                status, content_type, data = gateway.handle(
                    self.path, self.headers.get("Authorization", ""), raw)
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except OSError:
                return

    with HTTPServer((host, port), Handler) as server:
        write(out / "gateway.json", {"status": "listening", "config": cfg,
              "model": model, "upstream": UPSTREAM, "free_mode_confirmed": True})
        server.serve_forever()
