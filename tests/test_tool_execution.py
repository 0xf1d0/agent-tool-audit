import json
import tempfile
import unittest
from pathlib import Path

from auditlab.evidence import normalize_opencode, inventory
from auditlab.io import lines


class ToolExecutionTests(unittest.TestCase):
    def test_truncated_call_is_not_execution_and_metadata_drift_is_unknown(self):
        # Shape observed in pinned v2 real trace: providerResult.executed=false.
        events = []
        for i, metadata in enumerate(({'providerResult': {'executed': False}}, None, [])):
            events.append({'type': 'tool_use', 'part': {'id': str(i), 'tool': 'write',
                'state': {'status': 'error', 'input': {}, 'metadata': metadata}}})
        with tempfile.TemporaryDirectory() as d:
            raw, out = Path(d) / 'raw', Path(d) / 'normalized'
            raw.write_text(''.join(json.dumps(e) + '\n' for e in events))
            normalize_opencode(raw, out)
            rows = list(lines(out))
            self.assertEqual([r['execution_state'] for r in rows],
                             ['not_executed', 'unknown', 'unknown'])
            self.assertTrue(all(r['permission_state'] == 'unknown' for r in rows))
            risk = Path(d) / 'risk.json'
            risk.write_text('{}')
            item = inventory(out, risk, Path(d) / 'inventory.json')[0]
            self.assertEqual(item['completed_executions'], 0)
            self.assertEqual(item['known_not_executed'], 1)
            self.assertEqual(item['execution_unknown'], 2)
