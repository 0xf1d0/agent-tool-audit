import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_mistral_images
import mistral_preflight
import run_mistral_baseline
from auditlab import external
from auditlab.io import digest, load, write


class LabPreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def preparation(self):
        prep = self.root / 'prep'
        (prep / 'build-context').mkdir(parents=True)
        (prep / 'build-context/opencode.json').write_text('{}')
        (prep / 'prompt.txt').write_text('legitimate task')
        write(prep / 'baseline.json', {'models': ['mistral/model-a', 'mistral/model-b'],
            'task_id': 'fixture-not-real', 'policy_sha256': digest(prep / 'build-context/opencode.json'),
            'prompt_sha256': digest(prep / 'prompt.txt')})
        write(prep / 'image-build/build.json', {'builds': []})
        return prep

    def test_environment_file_is_data_never_shell_code(self):
        p = self.root / 'env'
        p.write_text('MISTRAL_API_KEY="$(touch /tmp/never-execute-auditlab)"\n'
                     'MISTRAL_FREE_ONLY_CONFIRMED=true\nOTHER_SECRET=ignore\n')
        with patch.dict('os.environ', {}, clear=True):
            result = mistral_preflight.settings(p)
        self.assertEqual(result['MISTRAL_API_KEY'], '$(touch /tmp/never-execute-auditlab)')
        self.assertEqual(set(result), {'MISTRAL_API_KEY', 'MISTRAL_FREE_ONLY_CONFIRMED'})

    def test_environment_overrides_local_file_without_logging_key(self):
        p = self.root / 'env'
        p.write_text('MISTRAL_API_KEY=file-value\n')
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'process-value'}, clear=True):
            result = mistral_preflight.preflight(self.root / 'preflight', env_file=p)
        self.assertTrue(result['credential_available'])
        self.assertNotIn('process-value', json.dumps(result))
        self.assertIsNone(result['remaining_tokens'])

    def test_build_rejects_mutable_base_before_docker(self):
        with self.assertRaises(ValueError), patch('subprocess.run') as execute:
            build_mistral_images.build(self.root, 'oven/bun:latest', 'python:latest', execute=True)
        execute.assert_not_called()

    def test_dry_baseline_does_not_invent_ready_image_or_outcomes(self):
        prep = self.preparation()
        with patch('subprocess.run') as execute:
            result = run_mistral_baseline.run(prep, self.root / 'dry', 'mistral/model-a')
        execute.assert_not_called()
        self.assertEqual(result['status'], 'blocked_image_build')
        trial = load(self.root / 'dry/trial.json')
        self.assertEqual(trial['status'], 'not_run')
        self.assertIsNone(trial['task_success'])
        self.assertIsNone(trial['attack_success'])

    def test_policy_drift_blocks_trial(self):
        prep = self.preparation()
        (prep / 'build-context/opencode.json').write_text('{"permission":"allow"}')
        with self.assertRaises(ValueError), patch('subprocess.run') as execute:
            run_mistral_baseline.run(prep, self.root / 'drift', 'mistral/model-a', execute=True)
        execute.assert_not_called()

    def test_full_verifier_summary_and_wrong_denominators(self):
        summary = {'tests': 2, 'passed': 2, 'failed': 0, 'skipped': 0, 'pending': 0, 'other': 0}
        outcome = lambda s, code=0: run_mistral_baseline.benchmark_outcome({'results': {'summary': s}}, code)
        self.assertTrue(outcome(summary))
        self.assertFalse(outcome({**summary, 'passed': 1, 'failed': 1}))
        self.assertFalse(outcome({**summary, 'passed': 1, 'skipped': 1}))
        self.assertIsNone(outcome({**summary, 'tests': 3}))
        self.assertIsNone(outcome({**summary, 'passed': '2'}))
        self.assertIsNone(outcome({**summary, 'tests': 0, 'passed': 0}))
        self.assertIsNone(run_mistral_baseline.benchmark_outcome({}, 0))

    def test_agent_has_no_provider_key_or_external_dns_forwarder(self):
        cmd = external.docker_command('sha256:' + 'a' * 64, self.root, 'mistral/model-a',
            'task', 'trial', network='private', env_names=['AUDITLAB_GATEWAY_TOKEN'], standalone=True)
        self.assertEqual(cmd[cmd.index('--dns') + 1], '127.0.0.1')
        self.assertNotIn('MISTRAL_API_KEY', cmd)
        self.assertEqual(cmd.count('--mount'), 1)

    def test_fixed_title_avoids_auxiliary_generation_and_preserves_prompt_argument(self):
        command = external.docker_command('sha256:' + 'a' * 64, self.root, 'mistral/model-a',
            'literal task; text', 'trial', standalone=True, title='Task')
        self.assertEqual(command[command.index('--title') + 1], 'Task')
        self.assertEqual(command[-1], 'literal task; text')

    def test_ownership_helper_is_isolated_and_does_not_follow_symlinks(self):
        image = 'sha256:' + 'a' * 64
        command = run_mistral_baseline.workspace_command(image, self.root, '1000:1000')
        self.assertEqual(command[command.index('--network') + 1], 'none')
        self.assertIn('--cap-add=CHOWN', command)
        self.assertEqual(command[-3:], ['-hR', '1000:1000', '/work'])
        self.assertEqual(command.count('--mount'), 1)
        with self.assertRaises(ValueError):
            run_mistral_baseline.workspace_command(image, self.root, '0:0; invalid')


if __name__ == '__main__':
    unittest.main()
