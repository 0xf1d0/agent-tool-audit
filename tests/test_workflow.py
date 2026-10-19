import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from auditlab import catalog, demo, evidence, external, metrics, planning, report
from auditlab.io import load, lines, write, jsonl
ROOT = Path(__file__).resolve().parents[1]

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def demo(self): return demo.run_demo(self.root / 'demo')
    def row(self): return next(lines(self.demo() / 'runs.jsonl'))
    def test_demo_four_controls(self):
        out=self.demo(); rows=list(lines(out/'runs.jsonl'))
        self.assertEqual(len(rows),4)
        self.assertEqual([(r['tool_version'],r['input_kind']) for r in rows if r['attack_success']], [('vulnerable','adversarial')])
        self.assertTrue(all(r['task_success'] for r in rows))
        self.assertEqual(load(out/'provenance.json')['llm_calls'],0)
    def test_no_overwrite(self):
        out=self.demo()
        with self.assertRaises(ValueError): demo.run_demo(out)
    def test_unknown_not_failure(self):
        row=self.row(); row.update(input_kind='adversarial',attack_success=None,task_success=None,status='timeout')
        jsonl(self.root/'rows',[row]); g=metrics.summarize(self.root/'rows',self.root/'summary')[0]
        self.assertIsNone(g['run_level_asr']['rate']); self.assertEqual(g['run_level_asr']['unknown'],1)
        self.assertIsNone(g['measured_cost_usd'])
    def test_duplicate_ids_rejected(self):
        row=self.row(); jsonl(self.root/'rows',[row,row])
        with self.assertRaises(ValueError): metrics.summarize(self.root/'rows',self.root/'summary')
    def test_boolean_strings_rejected(self):
        row=self.row(); row['attack_success']='false'
        with self.assertRaises(ValueError): metrics.validate(row)
    def test_nonfinite_cost_rejected(self):
        row=self.row(); row['cost_usd']=float('nan')
        with self.assertRaises(ValueError): metrics.validate(row)
    def test_benign_is_not_asr(self):
        groups=load(self.demo()/'summary.json')['groups']
        self.assertTrue(all(g['run_level_asr'] is None for g in groups if g['input_kind']=='benign'))
    def test_sarif_unverified(self):
        r=evidence.ingest_sarif(ROOT/'examples/synthetic.sarif.json',self.root/'findings')[0]
        self.assertEqual(r['cwe_candidates'],['CWE-22']); self.assertEqual(r['status'],'candidate')
        self.assertEqual(r['tool'],'SYNTHETIC-NOT-CODEQL')
    def test_review_packet_unknown(self):
        evidence.ingest_sarif(ROOT/'examples/synthetic.sarif.json',self.root/'findings')
        evidence.review_packets(self.root/'findings',self.root/'packets')
        p=load(next((self.root/'packets').glob('*.json')))
        self.assertEqual(p['response_template']['verdict'],'unknown')

    def test_sarif_same_line_distinct_columns_remain_distinct(self):
        data=load(ROOT/'examples/synthetic.sarif.json')
        original=data['runs'][0]['results'][0]
        import copy
        other=copy.deepcopy(original)
        original['locations'][0]['physicalLocation']['region'].update(startColumn=31,endColumn=53)
        other['locations'][0]['physicalLocation']['region'].update(startColumn=58,endColumn=80)
        data['runs'][0]['results']=[original,other]
        write(self.root/'sarif',data)
        rows=evidence.ingest_sarif(self.root/'sarif',self.root/'findings')
        self.assertEqual(len({r['finding_id'] for r in rows}),2)
        self.assertEqual([r['column'] for r in rows],[31,58])
        evidence.review_packets(self.root/'findings',self.root/'packets')
        self.assertEqual(len(list((self.root/'packets').glob('*.json'))),2)

    def test_duplicate_findings_cannot_silently_overwrite_packets(self):
        row={'finding_id':'duplicate','status':'candidate'}
        jsonl(self.root/'findings',[row,row])
        with self.assertRaises(ValueError):
            evidence.review_packets(self.root/'findings',self.root/'packets')
        self.assertFalse((self.root/'packets').exists())
    def test_agreement_not_confirmation(self):
        a={'finding_id':'a','model':'reviewer-a','verdict':'supported','cwes':['CWE-22'],'evidence':[]}
        jsonl(self.root/'a',[a]); jsonl(self.root/'b',[{**a,'model':'reviewer-b'}])
        r=evidence.compare_reviews(self.root/'a',self.root/'b',self.root/'cmp')[0]
        self.assertTrue(r['verdict_agreement']); self.assertEqual(r['runtime_validation'],'not_established')
    def test_review_ids_must_match(self):
        a={'finding_id':'a','model':'reviewer-a','verdict':'unknown','cwes':[],'evidence':[]}
        jsonl(self.root/'a',[a]); jsonl(self.root/'b',[{**a,'finding_id':'b','model':'reviewer-b'}])
        with self.assertRaises(ValueError): evidence.compare_reviews(self.root/'a',self.root/'b',self.root/'cmp')
    def test_trace_dedup_and_permission_unknown(self):
        event=next(lines(ROOT/'examples/opencode-events.jsonl'))
        jsonl(self.root/'raw',[event,event,{'type':'text'}])
        c=evidence.normalize_opencode(self.root/'raw',self.root/'trace')
        self.assertEqual(c['normalized_calls'],1); self.assertEqual(c['duplicate_terminal_events'],1)
        self.assertEqual(next(lines(self.root/'trace'))['permission_state'],'unknown')
    def test_unknown_trace_shape(self):
        jsonl(self.root/'raw',[{'type':'tool_use','part':{}}])
        c=evidence.normalize_opencode(self.root/'raw',self.root/'trace')
        self.assertEqual(c['unsupported_tool_events'],1)
    def test_unknown_tool_not_low_risk(self):
        jsonl(self.root/'trace',[{'tool':'unmapped'}])
        r=evidence.inventory(self.root/'trace',ROOT/'configs/risk.json',self.root/'inventory')[0]
        self.assertIsNone(r['priority_score'])
    def test_dataset_source_label_retained(self):
        write(self.root/'pairs',[{'method_change_id':'1','code_before':'before','code_after':'after','repo_name':'org/project','file_path':'a.c'}])
        r=evidence.import_pairs(self.root/'pairs',self.root/'normalized')[0]
        self.assertEqual(r['label_status'],'source_label_unverified'); self.assertEqual(r['split_group'],'org/project')
    def test_unresolved_plan_rejected(self):
        with self.assertRaises(ValueError): planning.plan(ROOT/'configs/pilot.template.json',self.root/'matrix')
    def test_plan_72_not_run(self):
        cfg={'tasks':['a','b','c'],'models':['p/a','p/b'],'repetitions':3,'versions':['vulnerable','patched'],'inputs':['benign','adversarial']}
        write(self.root/'cfg',cfg); rows=planning.plan(self.root/'cfg',self.root/'matrix')
        self.assertEqual(len(rows),72); self.assertEqual(len({r['run_id'] for r in rows}),72)
        self.assertTrue(all(r['status']=='not_run' for r in rows))
    def test_docker_argument_boundaries(self):
        c=external.docker_command('image@sha256:'+'a'*64,self.root,'p/m','a; $(echo example)','test')
        self.assertIn('--read-only',c); self.assertIn('--cap-drop=ALL',c)
        self.assertEqual(c[-1],'a; $(echo example)'); self.assertEqual(c.count('--mount'),1)
    def test_docker_rejects_mutable_image_and_host_network(self):
        with self.assertRaises(ValueError): external.docker_command('image:latest',self.root,'p/m','prompt','test')
        with self.assertRaises(ValueError): external.docker_command('image@sha256:'+'a'*64,self.root,'p/m','prompt','test','host')
    def test_dry_run_has_no_oracle(self):
        task=self.root/'task';task.mkdir(); prompt=self.root/'prompt';prompt.write_text('task')
        r=external.run_opencode('image@sha256:'+'a'*64,task,'p/m',prompt,self.root/'run')
        self.assertEqual(r['status'],'planned');self.assertEqual(r['oracle_status'],'not_collected')
        self.assertFalse((self.root/'run/raw.jsonl').exists())
    def test_evidence_not_in_agent_workspace(self):
        prompt=self.root/'prompt';prompt.write_text('task')
        with self.assertRaises(ValueError): external.run_opencode('image@sha256:'+'a'*64,self.root,'p/m',prompt,self.root/'out')
    def test_html_escaping(self):
        out=self.demo();data=load(out/'summary.json');data['groups'][0]['model']='<script>evil</script>'
        write(out/'summary.json',data);report.report(out/'summary.json',out/'report.html')
        text=(out/'report.html').read_text();self.assertNotIn('<script>',text);self.assertIn('&lt;script&gt;',text)
    def test_task_shortfall_and_escape(self):
        src=self.root/'benchmark';src.mkdir();(src/'task.md').write_text('task')
        subprocess.run(['git','init','-q',str(src)],check=True)
        subprocess.run(['git','-C',str(src),'add','.'],check=True)
        subprocess.run(['git','-C',str(src),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
        csv=self.root/'tasks.csv';header='task_id,domain,difficulty,task_path,selection_reason\n'
        csv.write_text(header+'a,software-engineering,easy,task.md,pilot\n')
        with self.assertRaises(ValueError):catalog.select(csv,src,20,self.root/'selection')
        self.assertEqual(len(catalog.select(csv,src,1,self.root/'selection')['tasks']),1)
        csv.write_text(header+'a,software-engineering,easy,../tasks.csv,pilot\n')
        with self.assertRaises(ValueError):catalog.select(csv,src,1,self.root/'selection2')


class FailureRecordingTests(unittest.TestCase):
    def test_cleanup_timeout_preserves_execution(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); task=root/'task'; task.mkdir(); prompt=root/'prompt'; prompt.write_text('task')
            effects=[subprocess.CompletedProcess([],0),subprocess.TimeoutExpired(['docker','rm'],30)]
            with patch('auditlab.external.shutil.which',return_value='/fake/docker'), patch('auditlab.external.subprocess.run',side_effect=effects):
                external.run_opencode('image@sha256:'+'a'*64,task,'p/m',prompt,root/'run',execute=True)
            record=load(root/'run/execution.json')
            self.assertEqual(record['status'],'completed')
            self.assertEqual(record['cleanup']['status'],'unknown')
            self.assertIn('wall_seconds',record)
    def test_codeql_timeout_is_recorded(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=root/'source';source.mkdir()
            with patch('auditlab.external.subprocess.check_output',side_effect=['a'*40,'','{}']), patch('auditlab.external.shutil.which',return_value='/fake/codeql'), patch('auditlab.external.subprocess.run',side_effect=subprocess.TimeoutExpired(['codeql'],3600)):
                with self.assertRaises(ValueError): external.codeql_plan(source,'python',root/'scan',execute=True)
            self.assertEqual(load(root/'scan/plan.json')['status'],'timeout')
    def test_unexecuted_outcomes_and_invalid_permission_rejected(self):
        r=load(ROOT/'examples/run-record.json')
        r['attack_success']=True
        with self.assertRaises(ValueError):metrics.validate(r)
        r['attack_success']=None;r['permission_state']='assumed_safe'
        with self.assertRaises(ValueError):metrics.validate(r)

if __name__=='__main__': unittest.main()
