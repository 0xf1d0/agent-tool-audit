"""Build only the minimal prepared context; pin resulting local image IDs."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditlab.io import load, write


def build(preparation, bun_image, python_image, execute=False, output=None):
    for image in (bun_image, python_image):
        if not re.fullmatch(r'[\w./:-]+@sha256:[0-9a-f]{64}', image):
            raise ValueError('Base images must be immutable registry digest references')
    prep = Path(preparation).resolve()
    metadata = load(prep / 'baseline.json')
    out = Path(output).resolve() if output else prep / 'image-build'
    out.mkdir(exist_ok=False)
    commands = []
    for target in ('agent', 'verifier', 'gateway'):
        tag = 'auditlab-' + target + ':' + metadata['framework']['commit'][:12]
        command = ['docker', 'build', '--platform', 'linux/amd64', '--target', target,
            '--build-arg', 'BUN_IMAGE=' + bun_image, '--build-arg', 'PYTHON_IMAGE=' + python_image,
            '--build-arg', 'FRAMEWORK_COMMIT=' + metadata['framework']['commit'],
            '--build-arg', 'FRAMEWORK_VERSION=' + metadata['framework']['version'],
            '--iidfile', str(out / (target + '.iid')), '--tag', tag, str(prep / 'build-context')]
        commands.append({'target': target, 'tag': tag, 'command': command, 'status': 'not_run', 'image': None})
    record = {'bun_image': bun_image, 'python_image': python_image, 'builds': commands}
    write(out / 'build.json', record)
    if execute:
        for row in commands:
            with (out / (row['target'] + '.log')).open('w') as log:
                try:
                    proc = subprocess.run(row['command'], stdout=log, stderr=subprocess.STDOUT, timeout=1800)
                    row.update(exit_code=proc.returncode, status='completed' if proc.returncode == 0 else 'error')
                except (OSError, subprocess.TimeoutExpired):
                    row['status'] = 'error_or_timeout'
                if row['status'] == 'completed':
                    row['image'] = (out / (row['target'] + '.iid')).read_text().strip()
                    if not re.fullmatch(r'sha256:[0-9a-f]{64}', row['image']):
                        row['status'] = 'invalid_image_id'
                write(out / 'build.json', record)
                if row['status'] != 'completed':
                    raise ValueError('Image build failed; inspect the recorded log')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preparation', required=True)
    parser.add_argument('--bun-image', required=True)
    parser.add_argument('--python-image', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--out', help='Fresh build evidence directory; never reuse an existing one')
    args = parser.parse_args()
    try:
        build(args.preparation, args.bun_image, args.python_image, args.execute, args.out)
    except (OSError, ValueError) as exc:
        parser.exit(2, str(exc) + '\n')
