"""Prepare inspected current SkillsBench sources without executing task code."""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditlab import catalog
from auditlab.io import digest, fresh, write


def source(root):
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip()
    if dirty:
        raise ValueError('Source checkout must be clean')
    return {'url': subprocess.check_output(['git', '-C', str(root), 'remote', 'get-url', 'origin'], text=True).strip(),
            'commit': commit, 'clean': True, 'license_sha256': digest(root / 'LICENSE')}


def prepare(out, opencode_config=ROOT / 'configs/opencode-v2.baseline.json',
            gateway_config=ROOT / 'configs/mistral-free.gateway.json'):
    out = fresh(out).resolve()
    framework, benchmark = ROOT / 'vendor/opencode', ROOT / 'vendor/skillsbench'
    sources = {'framework': source(framework), 'benchmark': source(benchmark),
               'revision_rule': 'Latest default branch at this session fetch time, then frozen',
               'task_selection_rule': 'Primary software-engineering category; easy before medium, then task ID; instruction/environment/verifier files present. Runtime reproducibility still unverified.'}
    write(out / 'sources.json', sources)
    rows, inspections = [], []
    for instruction in sorted((benchmark / 'tasks').glob('*/task.md')):
        text = instruction.read_text()
        if not text.startswith('---\n'):
            raise ValueError('Unknown task metadata format')
        header = text.split('---', 2)[1]
        category = re.search(r'^  category: ([^\n]+)$', header, re.M)
        difficulty = re.search(r'^  difficulty: ([^\n]+)$', header, re.M)
        if not category or not difficulty:
            raise ValueError('Missing task category/difficulty')
        if category[1] != 'software-engineering':
            continue
        task = instruction.parent
        required = [task / p for p in ('environment/Dockerfile', 'verifier/test.sh', 'verifier/test_outputs.py')]
        present = all(p.is_file() for p in required)
        inspections.append({'task_id': task.name, 'difficulty': difficulty[1],
            'instruction_sha256': digest(instruction), 'required_files_present': present,
            'files': {str(p.relative_to(benchmark)): digest(p) for p in required if p.is_file()},
            'runtime_validated': None, 'utility_validated': None,
            'inspection': 'Source inspection only; moving base tags, network installers and task-specific path requirements need isolated build verification.'})
        if difficulty[1] in ('easy', 'medium') and present:
            rows.append({'task_id': task.name, 'domain': 'software-engineering',
                'difficulty': difficulty[1], 'task_path': str(instruction.relative_to(benchmark)),
                'selection_reason': 'Primary SWE easy/medium; legitimate instruction and environment/verifier sources inspected; runtime pending.'})
    rows.sort(key=lambda r: (0 if r['difficulty'] == 'easy' else 1, r['task_id']))
    with (out / 'task-catalog.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['task_id', 'domain', 'difficulty', 'task_path', 'selection_reason'])
        writer.writeheader()
        writer.writerows(rows)
    write(out / 'task-inspection.json', inspections)
    try:
        catalog.select(out / 'task-catalog.csv', benchmark, 20, out / 'selection-20.json')
    except ValueError as exc:
        write(out / 'selection-shortage.json', {'target': 20, 'eligible_by_static_curation': len(rows),
              'error': str(exc), 'deviation': 'Use three-task staged pilot; runtime compatibility unverified.'})
    selected = catalog.select(out / 'task-catalog.csv', benchmark, 3, out / 'selection-3.json')
    if selected['tasks'][0]['task_id'] != 'dialogue-parser':
        raise ValueError('First-task recipe needs reinspection for this source revision')
    task = benchmark / 'tasks/dialogue-parser'
    context = out / 'build-context'
    context.mkdir()
    with (context / 'opencode.tar').open('wb') as f:
        subprocess.run(['git', '-C', str(framework), 'archive', '--format=tar', '--prefix=opencode/', 'HEAD'], stdout=f, check=True)
    shutil.copy(ROOT / 'runtime/mistral/Dockerfile', context / 'Dockerfile')
    shutil.copy(ROOT / 'runtime/mistral/opencode-launch', context / 'opencode-launch')
    shutil.copy(opencode_config, context / 'opencode.json')
    shutil.copy(gateway_config, context / 'gateway.json')
    shutil.copytree(ROOT / 'auditlab', context / 'auditlab', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(task / 'verifier', context / 'verifier')
    # Keep acting input and controller-only verifier physically separate.
    initial = out / 'initial-input'
    initial.mkdir()
    shutil.copy(task / 'environment/script.txt', initial / 'script.txt')
    body = (task / 'task.md').read_text().split('---', 2)[2].lstrip()
    (out / 'prompt.txt').write_text(body)
    version = json.loads((framework / 'package.json').read_text())['version']
    cfg = json.loads((ROOT / 'configs/pilot.template.json').read_text())
    cfg.update(tasks=[r['task_id'] for r in selected['tasks']],
        models=['mistral/' + m for m in json.loads((context / 'gateway.json').read_text())['models']],
        framework_commit=sources['framework']['commit'], benchmark_commit=sources['benchmark']['commit'],
        policy_sha256=digest(context / 'opencode.json'), image='REQUIRED_BUILT_IMAGE_ID')
    write(out / 'pilot.unresolved.json', cfg)
    write(out / 'baseline.json', {'status': 'blocked_runtime_and_free_account',
        'framework': {**sources['framework'], 'version': version}, 'benchmark': sources['benchmark'],
        'task_id': 'dialogue-parser', 'models': cfg['models'], 'review_models': cfg['models'],
        'model_access_verified': None, 'model_list_verified': None, 'review_sessions': 'independent', 'repetitions': 1,
        'tool_version': 'pinned_upstream', 'input_kind': 'benign', 'image': None,
        'bun_image': None, 'python_image': None, 'policy_sha256': cfg['policy_sha256'],
        'prompt_sha256': digest(out / 'prompt.txt'), 'gateway_config_sha256': digest(context / 'gateway.json'),
        'framework_archive_sha256': digest(context / 'opencode.tar'),
        'upstream_verifier_sha256': digest(task / 'verifier/test_outputs.py'),
        'budget': json.loads((context / 'gateway.json').read_text()), 'billed_cost_usd': None,
        'free_mode_confirmed': None, 'account_remaining_tokens': None,
        'utility': 'All pinned verifier checks pass, no skipped checks; process exit alone is insufficient.',
        'utility_limit': 'Upstream dialogue verifier checks files/graph/content but does not test the requested parse_script function; record benchmark coverage limitation.',
        'deviations': ['One task/two actors/one repetition first due to scarce free quota.',
            'No benchmark skills supplied in first baseline; models, task and policy held fixed.',
            'Dialogue /app path preserved by image symlink to /work.',
            'Verifier dependencies preinstalled; network installers from test.sh replaced with the same pinned pytest packages.'],
        'runtime_checks_needed': ['CLI help in built image', 'v2 config acceptance', 'read-only-root cache compatibility',
            'actual event fixture: v2 emits part.id rather than v1 callID', 'gateway provider SSE/usage compatibility',
            'internal network direct-egress denial and gateway-only access', 'trusted verifier unchanged script.txt']})
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--opencode-config', default=str(ROOT / 'configs/opencode-v2.baseline.json'))
    p.add_argument('--gateway-config', default=str(ROOT / 'configs/mistral-free.gateway.json'))
    a = p.parse_args()
    print(prepare(a.out, a.opencode_config, a.gateway_config))
