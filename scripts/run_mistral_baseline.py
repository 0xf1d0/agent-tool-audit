"""One benign trial on isolated networks; no provider key in the acting container."""
import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditlab import external
from auditlab.io import digest, fresh, load, write
from mistral_preflight import settings


def benchmark_outcome(ctrf, exit_code):
    summary = ctrf.get('results', {}).get('summary', {}) if isinstance(ctrf, dict) else {}
    if not isinstance(summary, dict):
        return None
    fields = ('tests', 'passed', 'failed', 'skipped', 'pending', 'other')
    if not all(type(summary.get(k)) is int and summary[k] >= 0 for k in fields):
        return None
    if summary['tests'] < 1 or summary['tests'] != sum(summary[k] for k in fields[1:]):
        return None
    return summary['tests'] == summary['passed'] and exit_code == 0


def workspace_command(image, workspace, owner=None):
    """Fixed, controller-only ownership helper, compatible with rootless UID maps."""
    command = ['run', '--rm', '--network', 'none', '--read-only', '--cap-drop=ALL',
               '--security-opt=no-new-privileges', '--user', '0:0',
               '--mount', 'type=bind,src=' + str(workspace) + ',dst=/work']
    if owner is None:
        return command + ['--entrypoint', 'stat', image, '-c', '%u:%g', '/work']
    if not re.fullmatch(r'[0-9]+:[0-9]+', owner):
        raise ValueError('Invalid disposable workspace owner')
    return command + ['--cap-add=CHOWN', '--entrypoint', 'chown', image, '-hR', owner, '/work']


def run(preparation, out, model, execute=False, build_record=None):
    prep = Path(preparation).resolve()
    out = fresh(out).resolve()
    cfg = load(prep / 'baseline.json')
    if model not in cfg['models']:
        raise ValueError('Select one of the two pinned acting models')
    if cfg['policy_sha256'] != digest(prep / 'build-context/opencode.json'):
        raise ValueError('Policy drift; prepare a new experiment bundle')
    if cfg['prompt_sha256'] != digest(prep / 'prompt.txt'):
        raise ValueError('Prompt drift; prepare a new experiment bundle')
    images = {r['target']: r['image'] for r in load(build_record or prep / 'image-build/build.json')['builds']
              if r['status'] == 'completed'}
    ready = all(re.fullmatch(r'sha256:[0-9a-f]{64}', images.get(name) or '')
                for name in ('agent', 'verifier', 'gateway'))
    write(out / 'trial.json', {'status': 'not_run', 'model': model, 'task_id': cfg['task_id'],
        'images': images, 'runtime_ready': ready, 'input_kind': 'benign', 'tool_version': 'pinned_upstream',
        'task_success': None, 'benchmark_task_success': None, 'attack_success': None,
        'permission_state': 'unknown', 'cost_usd': None})
    if not execute:
        return {'status': 'planned' if ready else 'blocked_image_build', 'out': str(out)}
    if not ready:
        raise ValueError('Complete and verify all three image builds first')
    values = settings()
    if values.get('MISTRAL_FREE_ONLY_CONFIRMED', '').lower() != 'true':
        raise ValueError('Free mode and disabled pay-as-you-go have not been confirmed in .env')
    if not values.get('MISTRAL_API_KEY'):
        raise ValueError('MISTRAL_API_KEY is missing')
    nonce = uuid.uuid4().hex[:10]
    internal, egress = 'auditlab-private-' + nonce, 'auditlab-egress-' + nonce
    gw, verifier = 'auditlab-gateway-' + nonce, 'auditlab-verifier-' + nonce
    token = secrets.token_urlsafe(32)
    env = {**os.environ, 'MISTRAL_API_KEY': values['MISTRAL_API_KEY'], 'AUDITLAB_GATEWAY_TOKEN': token}
    created_networks, created_containers = [], []
    actions = []
    owned_controller_directories = []

    def docker(args, check=True, timeout=60, credentials=False):
        command = ['docker', *args]
        try:
            result = subprocess.run(command, env=env if credentials else os.environ,
                                    capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            actions.append({'command': command, 'status': type(exc).__name__, 'exit_code': None})
            write(out / 'controller-actions.json', actions)
            raise
        actions.append({'command': command, 'exit_code': result.returncode})
        write(out / 'controller-actions.json', actions)
        if check and result.returncode:
            raise ValueError('Docker action failed; inspect controller-actions.json and daemon access')
        return result

    def cleanup(args):
        try:
            docker(args, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass  # Already recorded as unknown; preserve original trial outcome/error.

    def writable_evidence(path):
        path.mkdir()
        owner = docker(workspace_command(images['agent'], path)).stdout.strip()
        owned_controller_directories.append((path, owner))
        docker(workspace_command(images['agent'], path, '1000:1000'))
        return owner

    # Only the task workspace is ever bound into the actor, outside the research repo.
    with tempfile.TemporaryDirectory(prefix='auditlab-benign-') as task_directory:
        workspace = Path(task_directory) / 'work'
        shutil.copytree(prep / 'initial-input', workspace)
        original_owner = None
        try:
            for image in images.values():
                actual = docker(['image', 'inspect', '--format', '{{.Id}}', image]).stdout.strip()
                if actual != image:
                    raise ValueError('Image identity mismatch')
            original_owner = docker(workspace_command(images['agent'], workspace)).stdout.strip()
            docker(workspace_command(images['agent'], workspace, '1000:1000'))
            docker(['network', 'create', '--internal', internal])
            created_networks.append(internal)
            docker(['network', 'create', egress])
            created_networks.append(egress)
            gateway_evidence = out / 'gateway'
            writable_evidence(gateway_evidence)
            docker(['create', '--name', gw, '--network', egress, '--read-only', '--cap-drop=ALL',
                '--security-opt=no-new-privileges', '--pids-limit=64', '--memory=256m', '--cpus=1',
                '--user', '1000:1000', '--tmpfs', '/tmp:rw,nosuid,nodev,size=32m,mode=1777',
                '--mount', 'type=bind,src=' + str(gateway_evidence) + ',dst=/evidence',
                '--env', 'MISTRAL_API_KEY', '--env', 'AUDITLAB_GATEWAY_TOKEN', images['gateway'],
                '--model', model.split('/', 1)[1]], credentials=True)
            created_containers.append(gw)
            docker(['network', 'connect', '--alias', 'auditlab-gateway', internal, gw])
            docker(['start', gw])
            # Probe actual connectivity before supplying the acting prompt/token.
            probe = (
                'import socket,time\n'
                'for _ in range(15):\n'
                ' try:\n'
                '  socket.create_connection(("auditlab-gateway",8080),1).close();break\n'
                ' except OSError: time.sleep(0.2)\n'
                'else: raise SystemExit(2)\n'
                'for destination in ("api.mistral.ai","1.1.1.1"):\n'
                ' try: socket.create_connection((destination,443),2).close()\n'
                ' except OSError: continue\n'
                ' raise SystemExit(3)\n'
            )
            docker(['run', '--rm', '--network', internal, '--dns', '127.0.0.1', '--read-only',
                '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user', '1000:1000',
                '--entrypoint', 'python', images['agent'], '-c', probe])
            # external.run_opencode delegates to Docker with env NAMES, never provider values.
            old_token = os.environ.get('AUDITLAB_GATEWAY_TOKEN')
            os.environ['AUDITLAB_GATEWAY_TOKEN'] = token
            try:
                execution = external.run_opencode(images['agent'], workspace, model, prep / 'prompt.txt',
                    out / 'agent', network=internal, env_names=['AUDITLAB_GATEWAY_TOKEN'],
                    timeout=600, execute=True, standalone=True, title='Task')
            finally:
                if old_token is None:
                    os.environ.pop('AUDITLAB_GATEWAY_TOKEN', None)
                else:
                    os.environ['AUDITLAB_GATEWAY_TOKEN'] = old_token
            docker(workspace_command(images['agent'], workspace, original_owner))
            original_owner = None
            trial = load(out / 'trial.json')
            trial['status'] = execution['status']
            write(out / 'trial.json', trial)
            # Snapshot only data files used by the trusted upstream verifier. No actor code import.
            snapshot = out / 'verifier-input'
            snapshot.mkdir()
            actor_output = out / 'actor-output'
            actor_output.mkdir()
            for name in ('solution.py', 'dialogue.json', 'dialogue.dot'):
                path = workspace / name
                if path.is_file() and not path.is_symlink():
                    shutil.copyfile(path, actor_output / name)
            for name in ('dialogue.json', 'dialogue.dot'):
                path = workspace / name
                if path.is_file() and not path.is_symlink():
                    shutil.copyfile(path, snapshot / name)
            shutil.copyfile(prep / 'initial-input/script.txt', snapshot / 'script.txt')
            reports = out / 'verifier-reports'
            report_owner = writable_evidence(reports)
            docker(['create', '--name', verifier, '--network', 'none', '--read-only',
                '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user', '1000:1000',
                '--pids-limit=64', '--memory=512m', '--cpus=1',
                '--tmpfs', '/tmp:rw,nosuid,nodev,size=32m,mode=1777',
                '--mount', 'type=bind,src=' + str(snapshot) + ',dst=/work,readonly',
                '--mount', 'type=bind,src=' + str(reports) + ',dst=/reports', images['verifier']])
            created_containers.append(verifier)
            checked = docker(['start', '--attach', verifier], check=False, timeout=900)
            (out / 'verifier.stdout.txt').write_text(checked.stdout)
            (out / 'verifier.stderr.txt').write_text(checked.stderr)
            docker(workspace_command(images['agent'], reports, report_owner))
            owned_controller_directories.remove((reports, report_owner))
            benchmark_success = None
            if (reports / 'ctrf.json').is_file():
                try:
                    benchmark_success = benchmark_outcome(load(reports / 'ctrf.json'), checked.returncode)
                except (OSError, ValueError):
                    pass
            write(out / 'trial.json', {'status': execution['status'], 'model': model, 'task_id': cfg['task_id'],
                'images': images, 'input_kind': 'benign', 'tool_version': 'pinned_upstream',
                'benchmark_task_success': benchmark_success, 'task_success': None,
                'task_coverage_limit': cfg['utility_limit'], 'attack_success': None,
                'permission_state': 'unknown', 'cost_usd': None})
        finally:
            # Evidence lives in controller-only binds, surviving tmpfs/container shutdown.
            if gw in created_containers:
                cleanup(['stop', '--time', '2', gw])
            for container in reversed(created_containers):
                cleanup(['rm', '-f', container])
            for network in reversed(created_networks):
                cleanup(['network', 'rm', network])
            if original_owner is not None:
                cleanup(workspace_command(images['agent'], workspace, original_owner))
            for path, owner in reversed(owned_controller_directories):
                cleanup(workspace_command(images['agent'], path, owner))
    return {'out': str(out), 'status': load(out / 'trial.json')['status']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--preparation', required=True); p.add_argument('--out', required=True)
    p.add_argument('--model', required=True); p.add_argument('--execute', action='store_true')
    p.add_argument('--build-record', help='build.json from the successful fresh image build')
    a = p.parse_args()
    try:
        print(json.dumps(run(a.preparation, a.out, a.model, a.execute, a.build_record), indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        p.exit(2, 'Baseline stopped: ' + str(exc) + '\n')
