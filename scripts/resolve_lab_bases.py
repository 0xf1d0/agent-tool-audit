"""Resolve public Docker Hub base tags once; subsequent builds use digests."""
import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditlab.io import fresh, write


def resolve(out, node_only=False):
    out = fresh(out)
    record = {'status': 'resolving', 'images': {}}
    write(out / 'bases.json', record)
    images = [('node', 'library/node', '22.12.0-bookworm-slim')] if node_only else [
        ('bun', 'oven/bun', '1.4.2-debian'), ('python', 'library/python', '3.12.8-slim')]
    for role, repo, tag in images:
        query = urllib.parse.urlencode({'service': 'registry.docker.io', 'scope': 'repository:' + repo + ':pull'})
        with urllib.request.urlopen('https://auth.docker.io/token?' + query, timeout=30) as r:
            token = json.loads(r.read())['token']
        request = urllib.request.Request('https://registry-1.docker.io/v2/' + repo + '/manifests/' + tag, headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json'})
        with urllib.request.urlopen(request, timeout=30) as r:
            raw = r.read(4 * 1024 * 1024)
            digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
            if r.headers.get('Docker-Content-Digest') != digest:
                raise ValueError('Registry content digest mismatch')
            manifest = json.loads(raw)
        if not any(m.get('platform', {}).get('os') == 'linux' and m.get('platform', {}).get('architecture') == 'amd64'
                   for m in manifest.get('manifests', [])):
            raise ValueError('Base manifest lacks linux/amd64')
        record['images'][role] = {'tag_at_resolution': repo + ':' + tag, 'image': repo + '@' + digest}
        write(out / (role + '.manifest.json'), manifest)
        write(out / 'bases.json', record)
    record['status'] = 'resolved'
    write(out / 'bases.json', record)
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--node-only', action='store_true', help='Resolve the dedicated CodeQL Node.js analysis image')
    a = p.parse_args()
    try:
        print(json.dumps(resolve(a.out, a.node_only), indent=2))
    except (OSError, ValueError) as exc:
        p.exit(2, 'Base resolution failed: ' + type(exc).__name__ + '\n')
