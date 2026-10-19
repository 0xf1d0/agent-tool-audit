"""Read-only account/model preflight; never print or shell-source credentials."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditlab.io import fresh, write


def settings(env_file=ROOT / '.env'):
    values = {}
    if Path(env_file).is_file():
        for line in Path(env_file).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, sep, value = line.partition('=')
            if sep and key.strip() in {'MISTRAL_API_KEY', 'MISTRAL_FREE_ONLY_CONFIRMED'}:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key.strip()] = value
    for key in ('MISTRAL_API_KEY', 'MISTRAL_FREE_ONLY_CONFIRMED'):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def preflight(out, execute=False, env_file=ROOT / '.env', models=None):
    out = fresh(out)
    values = settings(env_file)
    models = models or ['mistral-small-2603', 'mistral-medium-3-5']
    record = {'status': 'planned', 'credential_available': bool(values.get('MISTRAL_API_KEY')),
        'free_only_confirmed': values.get('MISTRAL_FREE_ONLY_CONFIRMED', '').lower() == 'true',
        'models': {m: {'listed': None, 'capabilities': None, 'completion_verified': None} for m in models},
        'remaining_tokens': None, 'billed_cost_usd': None,
        'note': 'GET /v1/models only; no generation tokens requested. Account Limits/Subscriptions must be checked separately.'}
    write(out / 'preflight.json', record)
    if not execute:
        return record
    if not record['credential_available']:
        raise ValueError('MISTRAL_API_KEY is missing; configure .env locally or the process environment')
    request = urllib.request.Request('https://api.mistral.ai/v1/models', headers={
        'Authorization': 'Bearer ' + values['MISTRAL_API_KEY']})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read(4 * 1024 * 1024))
        if not isinstance(data, dict) or not isinstance(data.get('data'), list):
            raise ValueError('Model-list schema drift')
        entries = {m['id']: m for m in data['data'] if isinstance(m, dict) and isinstance(m.get('id'), str)}
        for model in models:
            record['models'][model].update(listed=model in entries,
                                          capabilities=entries.get(model, {}).get('capabilities'))
        record['status'] = 'model_list_received'
    except (OSError, ValueError) as exc:
        record['status'] = 'error'
        record['error_type'] = type(exc).__name__
        if isinstance(exc, urllib.error.HTTPError):
            record['http_status'] = exc.code
        write(out / 'preflight.json', record)
        raise ValueError('Mistral preflight failed; inspect non-secret preflight.json') from None
    write(out / 'preflight.json', record)
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--env-file', default=str(ROOT / '.env'))
    p.add_argument('--model', action='append')
    a = p.parse_args()
    try:
        print(json.dumps(preflight(a.out, a.execute, a.env_file, a.model), indent=2))
    except (ValueError, OSError) as exc:
        p.exit(2, str(exc) + '\n')
