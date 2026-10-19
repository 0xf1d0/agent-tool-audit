"""One bounded generation through the same paced gateway code as actor runs."""
import argparse
import hashlib
import json
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditlab.gateway import Gateway
from auditlab.io import fresh, load, write
from mistral_preflight import settings


def probe(config, model, kind, out, pacing_state):
    cfg = load(config)
    values = settings()
    if values.get('MISTRAL_FREE_ONLY_CONFIRMED', '').lower() != 'true':
        raise ValueError('Free-only confirmation required')
    out = fresh(out)
    Path(pacing_state).parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    gw = Gateway(cfg, token, values.get('MISTRAL_API_KEY', ''), out / 'usage.jsonl',
                 model, pacing_state=pacing_state)
    body = {'model': model, 'max_tokens': 16 if kind == 'completion' else 64,
            'messages': [{'role': 'user', 'content': 'Reply with exactly OK.' if kind == 'completion'
                         else 'Call record_marker with value ok.'}]}
    if kind == 'function':
        body.update(tools=[{'type': 'function', 'function': {'name': 'record_marker',
            'description': 'Return a test marker; no side effects.', 'parameters': {
                'type': 'object', 'properties': {'value': {'type': 'string', 'enum': ['ok']}},
                'required': ['value'], 'additionalProperties': False}}}], tool_choice='any')
    payload = json.dumps(body).encode()
    write(out / 'request.json', body)
    status, _, response = gw.handle('/v1/chat/completions', 'Bearer ' + token, payload)
    record = {'model': model, 'kind': kind, 'request_sha256': hashlib.sha256(payload).hexdigest(),
              'gateway_status': status, 'status': 'infrastructure_failure', 'response_valid': None,
              'usage': None, 'cost_usd': None, 'automatic_retries': 0}
    if status == 200:
        result = json.loads(response)
        write(out / 'response.json', result)
        record['usage'] = result['usage']
        try:
            message = result['choices'][0]['message']
            if kind == 'completion':
                record['exact_text_match'] = message['content'].strip() == 'OK'
                valid = isinstance(message['content'], str) and bool(message['content'].strip())
            else:
                calls = message['tool_calls']
                valid = (len(calls) == 1 and calls[0]['function']['name'] == 'record_marker'
                         and json.loads(calls[0]['function']['arguments']) == {'value': 'ok'})
            record.update(response_valid=valid, status='passed' if valid else 'model_response_failure')
        except (KeyError, TypeError, IndexError, ValueError):
            record.update(status='response_schema_failure', response_valid=None)
    write(out / 'probe.json', record)
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True); p.add_argument('--model', required=True)
    p.add_argument('--kind', choices=['completion', 'function'], required=True)
    p.add_argument('--out', required=True); p.add_argument('--pacing-state', required=True)
    a = p.parse_args()
    result = probe(a.config, a.model, a.kind, a.out, a.pacing_state)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['status'] == 'passed' else 2)
