import json
import tempfile
import unittest
from pathlib import Path

from auditlab.pacing import Pacer


class PacingTests(unittest.TestCase):
    def test_shared_spacing_and_rolling_token_window(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.json'
            now = [1000.0]
            sleep = lambda t: now.__setitem__(0, now[0] + t)
            def pacer():
                return Pacer(path, {'a': 100, 'b': 100}, clock=lambda: now[0], sleep=sleep)
            with pacer().slot('a', 80, 120) as e:
                e['usage'] = {'total_tokens': 80}
            with pacer().slot('b', 80, 120) as e:
                self.assertEqual(e['start'], 1003)
                e['usage'] = {'total_tokens': 80}
            with pacer().slot('a', 30, 120) as e:
                self.assertEqual(e['start'], 1060)
                e['usage'] = {'total_tokens': 20}
            state = json.loads(path.read_text())
            self.assertEqual(state['events'][-1]['tokens'], 20)
            self.assertFalse(state['blocked'])

    def test_unknown_usage_blocks_other_models_and_oversize_never_dispatches(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.json'
            p = Pacer(path, {'a': 100, 'b': 100})
            with self.assertRaises(ValueError):
                with p.slot('a', 101, 10):
                    self.fail('must not dispatch')
            with p.slot('a', 10, 10):
                pass
            with self.assertRaises(ValueError):
                with p.slot('b', 10, 10):
                    self.fail('unknown usage must block subsequent requests')
