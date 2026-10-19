import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_codeql_isolated


class CodeQLIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.tool = self.root / 'codeql'
        suite = self.tool / 'qlpacks/codeql/javascript-queries/2.4.7/codeql-suites/javascript-security-extended.qls'
        suite.parent.mkdir(parents=True)
        suite.write_text('# synthetic suite path for control-flow testing only')
        (self.tool / 'codeql').write_text('# synthetic executable; never executed')

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_has_read_only_sources_no_network_and_no_source_build(self):
        with patch('subprocess.check_output', side_effect=['a' * 40, '']), patch('subprocess.run') as execute:
            _, _, record = run_codeql_isolated.plan(self.source, self.tool, 'sha256:' + 'b' * 64,
                                                   'a' * 40, self.root / 'out')
        execute.assert_not_called()
        for command in record['commands']:
            self.assertEqual(command[command.index('--network') + 1], 'none')
            self.assertIn('--read-only', command)
            self.assertEqual(command.count('--mount'), 3)
            self.assertFalse(any('MISTRAL' in arg for arg in command))
        self.assertIn('--build-mode=none', record['commands'][1])
        self.assertIn('2.4.7', ' '.join(record['commands'][2]))
        self.assertEqual(record['status'], 'planned')

    def test_revision_drift_blocks_before_extraction(self):
        with patch('subprocess.check_output', return_value='c' * 40), patch('subprocess.run') as execute:
            with self.assertRaises(ValueError):
                run_codeql_isolated.plan(self.source, self.tool, 'sha256:' + 'b' * 64,
                                        'a' * 40, self.root / 'out')
        execute.assert_not_called()

    def test_database_reuse_requires_matching_extraction_provenance(self):
        previous = self.root / 'previous'
        database = previous / 'results/database'
        database.mkdir(parents=True)
        (database / 'codeql-database.yml').write_text('# synthetic metadata, never analyzed')
        (previous / 'plan.json').write_text(json.dumps({'source_commit': 'c' * 40,
                                                       'steps': [{'index': 1, 'exit_code': 0}]}))
        with patch('subprocess.check_output', side_effect=['a' * 40, '']), patch('subprocess.run') as execute:
            with self.assertRaises(ValueError):
                run_codeql_isolated.plan(self.source, self.tool, 'sha256:' + 'b' * 64,
                    'a' * 40, self.root / 'mismatched', reuse_database=database)
        execute.assert_not_called()
        (previous / 'plan.json').write_text(json.dumps({'source_commit': 'a' * 40,
                                                       'steps': [{'index': 1, 'exit_code': 1}]}))
        with patch('subprocess.check_output', side_effect=['a' * 40, '']):
            with self.assertRaises(ValueError):
                run_codeql_isolated.plan(self.source, self.tool, 'sha256:' + 'b' * 64,
                    'a' * 40, self.root / 'failed', reuse_database=database)

    def test_cache_is_persistent_and_pinned_database_can_be_reused(self):
        previous = self.root / 'previous'
        database = previous / 'results/database'
        database.mkdir(parents=True)
        (database / 'codeql-database.yml').write_text('# synthetic metadata, never analyzed')
        (previous / 'plan.json').write_text(json.dumps({'source_commit': 'a' * 40,
                                                       'steps': [{'index': 1, 'exit_code': 0}]}))
        cache = self.root / 'cache'
        cache.mkdir()
        (cache / 'fixture').write_text('synthetic cache bytes')
        with patch('subprocess.check_output', side_effect=['a' * 40, '']), patch('subprocess.run') as execute:
            out, results, record = run_codeql_isolated.plan(self.source, self.tool,
                'sha256:' + 'b' * 64, 'a' * 40, self.root / 'reuse', database, cache)
        execute.assert_not_called()
        self.assertTrue((results / 'database/codeql-database.yml').exists())
        self.assertTrue((results / 'common-caches/compile-cache/fixture').exists())
        self.assertIn('--common-caches=/results/common-caches', record['commands'][2])
