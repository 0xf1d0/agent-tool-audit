"""Pinned, network-free JavaScript extraction/analysis; no source build execution."""
import argparse
import json
import re
import subprocess
import shutil
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditlab.io import digest, fresh, write
from run_mistral_baseline import workspace_command


def plan(source, codeql, image, expected_commit, out, reuse_database=None, cache_seed=None):
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('Pinned local image ID required')
    source, codeql = Path(source).resolve(), Path(codeql).resolve()
    actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != expected_commit:
        raise ValueError('Source revision changed')
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Source checkout must be clean')
    suite = codeql / 'qlpacks/codeql/javascript-queries/2.4.7/codeql-suites/javascript-security-extended.qls'
    for p in (codeql / 'codeql', suite):
        if not p.is_file():
            raise ValueError('Pinned CodeQL installation/query suite missing')
    out = fresh(out).resolve()
    results = out / 'results'
    results.mkdir()
    if reuse_database is not None:
        previous = Path(reuse_database).resolve()
        provenance = json.loads((previous.parent.parent / 'plan.json').read_text())
        if (provenance.get('source_commit') != expected_commit
                or not any(s.get('index') == 1 and s.get('exit_code') == 0 for s in provenance.get('steps', []))
                or not (previous / 'codeql-database.yml').is_file()):
            raise ValueError('Reusable database needs matching source and completed extraction evidence')
        shutil.copytree(previous, results / 'database', symlinks=True)
    if cache_seed is not None:
        shutil.copytree(Path(cache_seed).resolve(), results / 'common-caches/compile-cache')
    base = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop=ALL',
        '--security-opt=no-new-privileges', '--pids-limit=256', '--memory=6g', '--cpus=2',
        '--user', '1000:1000', '--tmpfs', '/tmp:rw,nosuid,nodev,size=1g,mode=1777',
        '--env', 'HOME=/tmp/home', '--env', 'XDG_CACHE_HOME=/tmp/cache',
        '--mount', 'type=bind,src=' + str(source) + ',dst=/source,readonly',
        '--mount', 'type=bind,src=' + str(codeql) + ',dst=/opt/codeql,readonly',
        '--mount', 'type=bind,src=' + str(results) + ',dst=/results',
        '--entrypoint', '/bin/sh', image, '-c',
        'mkdir -p /tmp/home /tmp/cache; exec /opt/codeql/codeql "$@"', 'codeql']
    commands = [
        base + ['version', '--format=json', '--common-caches=/results/common-caches'],
        base + ['database', 'create', '/results/database', '--language=javascript-typescript',
                '--source-root=/source', '--build-mode=none', '--threads=2', '--ram=4096', '--common-caches=/results/common-caches'],
        base + ['database', 'analyze', '/results/database',
                '/opt/codeql/qlpacks/codeql/javascript-queries/2.4.7/codeql-suites/javascript-security-extended.qls',
                '--format=sarifv2.1.0', '--output=/results/findings.sarif', '--threads=2', '--ram=4096',
                '--no-sarif-add-snippets', '--sarif-include-query-help=never', '--common-caches=/results/common-caches'],
    ]
    record = {'source_commit': actual, 'image': image, 'codeql_path': str(codeql),
        'query_pack': 'codeql/javascript-queries@2.4.7', 'query_suite_sha256': digest(suite),
        'status': 'planned', 'commands': commands, 'steps': [],
        'reused_database': str(reuse_database) if reuse_database else None,
        'cache_seed': str(cache_seed) if cache_seed else None,
        'scope': 'Repository-wide provisional scan before tool exposure; Mistral generation rate-limited. No observed-tool priority or vulnerability confirmation implied.'}
    write(out / 'plan.json', record)
    return out, results, record


def run(source, codeql, image, expected_commit, out, execute=False, reuse_database=None, cache_seed=None):
    out, results, record = plan(source, codeql, image, expected_commit, out, reuse_database, cache_seed)
    if not execute:
        return record
    original = None
    actions = []

    def ownership(owner=None):
        command = ['docker', *workspace_command(image, results, owner)]
        r = subprocess.run(command, capture_output=True, text=True, timeout=60)
        actions.append({'command': command, 'exit_code': r.returncode})
        write(out / 'ownership.json', actions)
        if r.returncode:
            raise ValueError('CodeQL output ownership setup/restore failed')
        return r.stdout.strip()

    try:
        original = ownership()
        ownership('1000:1000')
        for index, command in enumerate(record['commands']):
            if index == 1 and reuse_database:
                record['steps'].append({'index': 1, 'status': 'reused_finalized_database', 'exit_code': 0})
                continue
            name = 'auditlab-codeql-' + uuid.uuid4().hex[:10]
            command = command[:2] + ['--name', name] + command[2:]
            record['commands'][index] = command
            record['status'] = 'running'
            write(out / 'plan.json', record)
            started = time.monotonic()
            step = {'index': index, 'exit_code': None}
            try:
                with (out / ('step-' + str(index) + '.log')).open('w') as log:
                    r = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
                step.update(exit_code=r.returncode, status='completed' if r.returncode == 0 else 'error')
            except (OSError, subprocess.TimeoutExpired) as exc:
                step['status'] = type(exc).__name__
            finally:
                step['wall_seconds'] = time.monotonic() - started
                record['steps'].append(step)
                record['status'] = step['status']
                write(out / 'plan.json', record)
                cleanup = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
                step['cleanup_exit_code'] = cleanup.returncode
            if step['status'] != 'completed':
                raise ValueError('CodeQL step failed; inspect preserved plan/logs')
        record['status'] = 'completed'
        record['sarif_sha256'] = digest(results / 'findings.sarif')
    finally:
        if original is not None:
            try:
                ownership(original)
            except (ValueError, OSError, subprocess.TimeoutExpired):
                record['ownership_restore'] = 'unknown'
        write(out / 'plan.json', record)
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True); p.add_argument('--codeql', default='/opt/codeql')
    p.add_argument('--image', required=True); p.add_argument('--expected-commit', required=True)
    p.add_argument('--out', required=True); p.add_argument('--execute', action='store_true')
    p.add_argument('--reuse-database'); p.add_argument('--cache-seed')
    a = p.parse_args()
    try:
        r = run(a.source, a.codeql, a.image, a.expected_commit, a.out, a.execute, a.reuse_database, a.cache_seed)
        print(json.dumps({'status': r['status']}))
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        p.exit(2, str(exc) + '\n')
