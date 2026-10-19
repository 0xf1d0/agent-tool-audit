import json
import io
import urllib.error
import tempfile
import unittest
from pathlib import Path

from auditlab import external, gateway
from auditlab.io import load, lines

ROOT = Path(__file__).resolve().parents[1]


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = load(ROOT / 'configs/mistral-free.gateway.json')
        self.token = 't' * 40
        self.calls = []
        self.response = json.dumps({'choices': [], 'usage': {
            'prompt_tokens': 10, 'completion_tokens': 2, 'total_tokens': 12}}).encode()
        self.g = gateway.Gateway(self.cfg, self.token, 'private-test-key',
                                 self.root / 'ledger', self.cfg['models'][0], self.forward)

    def tearDown(self):
        self.tmp.cleanup()

    def forward(self, body):
        self.calls.append(json.loads(body))
        return 200, 'application/json', self.response

    def request(self, **overrides):
        body = {'model': self.cfg['models'][0], 'messages': [{'role': 'user', 'content': 'task'}]}
        body.update(overrides)
        return self.g.handle('/v1/chat/completions', 'Bearer ' + self.token, json.dumps(body).encode())

    def test_token_route_and_session_model_are_enforced(self):
        self.assertEqual(self.g.handle('/v1/chat/completions', 'wrong', b'{}')[0], 401)
        self.assertEqual(self.g.handle('/v1/files', 'Bearer ' + self.token, b'{}')[0], 403)
        self.assertEqual(self.request(model=self.cfg['models'][1])[0], 400)
        self.assertEqual(self.calls, [])

    def test_no_remote_images_or_hidden_batch_fields(self):
        self.assertEqual(self.request(messages=[{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': 'https://private.invalid'}}]}])[0], 400)
        self.assertEqual(self.request(n=1000)[0], 400)
        self.assertEqual(self.request(max_tokens=True)[0], 400)
        self.assertEqual(self.calls, [])
        records = list(lines(self.root / 'ledger'))
        self.assertTrue(all(r['upstream_dispatched'] is False for r in records))
        self.assertIn('n', records[1]['request_keys'])

    def test_output_cap_usage_and_secret_boundary(self):
        self.assertEqual(self.request(max_tokens=999999)[0], 200)
        self.assertEqual(self.calls[0]['max_tokens'], self.cfg['max_output_tokens'])
        self.assertEqual(self.calls[0]['temperature'], 0)
        records = list(lines(self.root / 'ledger'))
        self.assertIsNone(records[0]['usage'])
        self.assertEqual(records[1]['usage']['total_tokens'], 12)
        self.assertIsNone(records[1]['cost_usd'])
        text = (self.root / 'ledger').read_text()
        self.assertNotIn(self.token, text)
        self.assertNotIn('private-test-key', text)
        self.assertNotIn('"content"', text)

    def test_live_v2_prompt_cache_field_is_supported_without_relaxing_model_limits(self):
        self.assertEqual(self.request(prompt_cache_key='public-session-id')[0], 200)
        self.assertEqual(self.calls[0]['prompt_cache_key'], 'public-session-id')
        self.assertEqual(self.request(prompt_cache_key='x' * 65)[0], 400)

    def test_request_and_reservation_caps_block_before_dispatch(self):
        self.g.cfg = {**self.cfg, 'max_requests': 1}
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.request()[0], 429)
        self.assertEqual(len(self.calls), 1)
        self.g = gateway.Gateway({**self.cfg, 'reservation_units': 1}, self.token, 'key',
                                 self.root / 'ledger2', self.cfg['models'][0], self.forward)
        self.assertEqual(self.request()[0], 429)
        self.assertEqual(len(self.calls), 1)

    def test_known_token_limit_and_expiry(self):
        self.g.cfg = {**self.cfg, 'observed_token_limit': 12}
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.request()[0], 429)
        self.g.clock = lambda: self.g.deadline
        self.assertEqual(self.request()[0], 403)

    def test_observed_token_stop_threshold_allows_final_request_overshoot(self):
        self.g.cfg = {**self.cfg, 'observed_token_limit': 20}
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.g.observed, 24)
        self.assertEqual(self.request()[0], 429)
        self.assertEqual(len(self.calls), 2)

    def test_final_serialized_payload_is_capped_not_only_inbound_bytes(self):
        self.g.cfg = {**self.cfg, 'max_request_bytes': 200}
        body = {'model': self.cfg['models'][0], 'messages': [{'role': 'user', 'content': ''}],
                'max_tokens': 1024, 'temperature': 0}
        body['messages'][0]['content'] = 'x' * (201 - len(json.dumps(body).encode()))
        raw = json.dumps(body, separators=(',', ':')).encode()
        self.assertLessEqual(len(raw), 200)
        status, _, _ = self.g.handle('/v1/chat/completions', 'Bearer ' + self.token, raw)
        self.assertEqual(status, 413)
        self.assertEqual(self.calls, [])
        self.assertFalse(list(lines(self.root / 'ledger'))[-1]['upstream_dispatched'])

    def test_paired_revision_consistency_and_four_maximum_serialized_requests(self):
        cfg = load(ROOT / 'configs/ministral-free.gateway.json')
        policy = load(ROOT / 'configs/opencode-v2.ministral.json')
        provider = policy['providers']['mistral']
        self.assertEqual(provider['body']['max_tokens'], cfg['max_output_tokens'])
        self.assertEqual(cfg['max_output_tokens'], 4096)
        self.assertEqual(cfg['max_requests'], policy['agents']['build']['steps'])
        self.assertEqual(cfg['max_requests'], 4)
        self.assertEqual(set(provider['models']), set(cfg['models']))
        self.assertTrue(all(m['limit']['output'] == 4096 for m in provider['models'].values()))
        bound = cfg['max_requests'] * (cfg['max_request_bytes'] + cfg['max_output_tokens'] + 4096)
        self.assertEqual(bound, 425984)
        self.assertEqual(cfg['reservation_units'], 524288)
        self.assertEqual(cfg['observed_token_limit'], 32768)
        # Isolate byte accounting from pacing; no real calls or sleeps in this test.
        cfg.pop('tokens_per_minute')
        self.g = gateway.Gateway(cfg, self.token, 'key', self.root / 'revision-ledger',
                                 cfg['models'][0], self.forward)
        body = {'model': cfg['models'][0], 'messages': [{'role': 'user', 'content': ''}],
                'max_tokens': 4096, 'temperature': 0}
        body['messages'][0]['content'] = 'x' * (cfg['max_request_bytes'] - len(json.dumps(body).encode()))
        raw = json.dumps(body).encode()
        self.assertEqual(len(raw), cfg['max_request_bytes'])
        for _ in range(4):
            self.assertEqual(self.g.handle('/v1/chat/completions', 'Bearer ' + self.token, raw)[0], 200)
        self.assertEqual(self.g.reserved, bound)
        self.assertEqual(self.g.handle('/v1/chat/completions', 'Bearer ' + self.token, raw)[0], 429)
        self.assertEqual(len(self.calls), 4)

    def test_missing_usage_or_provider_failure_stops_session(self):
        self.response = b'{"choices": []}'
        self.assertEqual(self.request()[0], 502)
        self.assertEqual(self.request()[0], 403)
        self.assertEqual(len(self.calls), 1)
        record = list(lines(self.root / 'ledger'))[-1]
        self.assertIsNone(record['usage'])
        self.assertEqual(record['status'], 'error_usage_unknown')

    def test_provider_rate_limit_is_not_retried(self):
        self.g.transport = lambda data: (429, 'application/json', b'{}')
        self.assertEqual(self.request()[0], 502)
        self.assertTrue(self.g.stopped)

    def test_http_quota_details_are_preserved_without_keys(self):
        def limited(data):
            raise urllib.error.HTTPError(gateway.UPSTREAM, 429, 'limited', {
                'Retry-After': '60', 'X-RateLimit-Reset': 'private-test-key', 'Authorization': 'secret'},
                io.BytesIO(b'{"message":"quota private-test-key"}'))
        self.g.transport = limited
        self.assertEqual(self.request()[0], 502)
        record = list(lines(self.root / 'ledger'))[-1]
        self.assertEqual(record['upstream_status'], 429)
        self.assertEqual(record['retry_after'], '60')
        self.assertEqual(record['rate_limit_headers']['X-RateLimit-Reset'], '[REDACTED]')
        self.assertNotIn('Authorization', record['rate_limit_headers'])
        self.assertNotIn('private-test-key', record['provider_error']['message'])
        self.assertIsNone(record['usage'])

    def test_exhausted_local_budget_stops_retries_without_upstream_calls(self):
        self.g.cfg = {**self.cfg, 'max_requests': 1}
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.request()[0], 429)
        self.assertEqual(self.request()[0], 403)
        self.assertEqual(len(self.calls), 1)
        last = list(lines(self.root / 'ledger'))[-1]
        self.assertEqual(last['status'], 'rejected_budget')
        self.assertFalse(last['upstream_dispatched'])

    def test_usage_schema_drift_and_wrong_denominator(self):
        for usage in [{'prompt_tokens': True, 'completion_tokens': 1, 'total_tokens': 2},
                      {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 3}]:
            with self.assertRaises(ValueError):
                gateway.provider_usage(json.dumps({'usage': usage}).encode(), 'application/json')

    def test_stream_usage_is_parsed_and_missing_usage_rejected(self):
        sse = b'data: {"choices":[]}\n\ndata: {"usage":{"prompt_tokens":1,"completion_tokens":2,"total_tokens":3}}\n\ndata: [DONE]\n'
        self.assertEqual(gateway.provider_usage(sse, 'text/event-stream')['total_tokens'], 3)
        with self.assertRaises(ValueError):
            gateway.provider_usage(b'data: [DONE]\n', 'text/event-stream')
        with self.assertRaises(ValueError):
            gateway.provider_usage(sse.replace(b'data: [DONE]\n', b''), 'text/event-stream')

    def test_free_confirmation_required_and_dry_run_has_no_key(self):
        result = gateway.serve(ROOT / 'configs/mistral-free.gateway.json', self.root / 'dry',
                               self.cfg['models'][0])
        self.assertEqual(result['status'], 'planned')
        with self.assertRaises(ValueError):
            gateway.serve(ROOT / 'configs/mistral-free.gateway.json', self.root / 'live',
                          self.cfg['models'][0], execute=True)

    def test_invalid_config_rejected(self):
        for update in ({'models': ['same', 'same']}, {'models': [{}, {}]},
                       {'free_only': False}, {'max_requests': True}):
            with self.assertRaises(ValueError):
                gateway.validate_config({**self.cfg, **update})

    def test_local_image_id_and_v2_private_server(self):
        cmd = external.docker_command('sha256:' + 'a' * 64, self.root, 'mistral/model',
                                      'task', 'trial', standalone=True)
        self.assertIn('--standalone', cmd)
        self.assertEqual(cmd.count('--mount'), 1)
        self.assertNotIn('--auto', cmd)
        self.assertNotIn('MISTRAL_API_KEY', cmd)
        with self.assertRaises(ValueError):
            external.docker_command('sha256:short', self.root, 'mistral/model', 'task', 'trial')
