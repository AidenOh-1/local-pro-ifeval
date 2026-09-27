import copy,json,tempfile,unittest,sys
from pathlib import Path
from local_pro_release import cli
sys.path.insert(0,str(cli.PACKAGE/'scripts'))
import plot_results

class ReportingTests(unittest.TestCase):
 def setUp(self):
  self.r=cli.PACKAGE;_,self.refs,self.s=cli.report_inputs(self.r,self.r/'results/v0.1/scores.json')
 def test_metrics(self):
  x=cli.summary(self.s,self.refs);self.assertEqual([(v['correct'],v['denominator']) for v in x['metrics'].values()],[(431,541),(715,834),(452,541),(740,834)])
 def test_duplicate(self):
  s=copy.deepcopy(self.s);s['items'].append(s['items'][0])
  with self.assertRaisesRegex(ValueError,'SCORE_UIDS'):cli.summary(s,self.refs)
 def test_denominator(self):
  s=copy.deepcopy(self.s);s['items'][0]['instruction_total']+=1
  with self.assertRaisesRegex(ValueError,'INSTRUCTION_DENOMINATOR'):cli.summary(s,self.refs)
 def test_gap(self):
  s=copy.deepcopy(self.s);s['items'].pop()
  with self.assertRaisesRegex(ValueError,'COVERAGE_GAP'):cli.summary(s,self.refs)
 def test_partial_is_not_full(self):
  s=copy.deepcopy(self.s);x=s['items'].pop();s['missing'].append(x['uid'])
  self.assertIsNone(cli.summary(s,self.refs)['metrics']['strict_prompt']['full_accuracy'])
 def test_duplicate_missing_rejected(self):
  s=copy.deepcopy(self.s);x=s['items'].pop();s['missing']=[x['uid'],x['uid']]
  with self.assertRaisesRegex(ValueError,'DUPLICATE_COVERAGE'):cli.summary(s,self.refs)
 def test_type(self):
  s=copy.deepcopy(self.s);s['items'][0]['strict_prompt']=1
  with self.assertRaisesRegex(ValueError,'PROMPT_CONJUNCTION'):cli.summary(s,self.refs)
 def test_schema(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.json';s=copy.deepcopy(self.s);s['schema']=9;cli.publish(p,s)
   with self.assertRaisesRegex(ValueError,'SCORE_SCHEMA'):cli.report_inputs(self.r,p)
 def test_no_mutation_and_example(self):
  paths=[self.r/'examples/verdicts.json',self.r/'examples/coverage.json'];before=[p.read_bytes() for p in paths]
  with tempfile.TemporaryDirectory() as d:
   x=cli.do_report(self.r,paths[0],Path(d)/'report',paths[1]);self.assertTrue(x['synthetic_example_not_benchmark']);self.assertEqual(x['metrics']['strict_instruction']['correct'],2)
  self.assertEqual(before,[p.read_bytes() for p in paths])
 def test_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';cli.publish(p,'a')
   with self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS'):cli.publish(p,'b')
 def test_optional_assets_and_authority(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'MISSING_EVALUATION_ASSET:data/ifeval.jsonl'):cli.do_run(self.r,Path(d)/'dry',True)
   with self.assertRaisesRegex(ValueError,'VALID_EXISTING_REGISTRATION_REQUIRED'):cli.do_run(self.r,Path(d)/'live',False)
 def test_length(self):
  rows=[r for r in self.s['items'] if r['finish_reason']=='length'];self.assertEqual((len(rows),sum(not r['strict_prompt'] for r in rows)),(9,4))
 def test_graph(self):
  import xml.etree.ElementTree as ET
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);plot_results.build(p)
   root=ET.parse(p/'ifeval.svg').getroot();values=[float(r.attrib['data-value']) for r in root.iter() if 'data-value' in r.attrib]
   self.assertEqual(len(values),4)
   for value,want in zip(values,[431/541*100,715/834*100,452/541*100,740/834*100]):self.assertAlmostEqual(value,want,8)
   self.assertIn('not a head-to-head comparison',(p/'external-context.svg').read_text())
   for name in ('ifeval.svg','external-context.svg'):self.assertEqual((p/name).read_bytes(),(self.r/'assets'/name).read_bytes())
 def test_external(self):
  x=cli.read(self.r/'results/external_references.json')
  self.assertEqual([(r['snapshot'],r['value']) for r in x['rows']],[('GPT-4 (API snapshot unspecified)',76.89),('GPT-4o-mini-2024-07-18',80.4),('GPT-4o 0513',84.3),('Claude-3.5-Sonnet-1022',86.5)])
  self.assertTrue(all(r['verified'] and r['exact_metric']=='IFEval English strict prompt accuracy' for r in x['rows']))
  import xml.etree.ElementTree as ET
  with tempfile.TemporaryDirectory() as d:
   plot_results.build(Path(d));svg=(Path(d)/'external-context.svg').read_text();root=ET.fromstring(svg)
   texts=[r.text for r in root.iter() if r.tag.endswith('text')]
   values=[float(r.attrib['data-value']) for r in root.iter() if 'data-value' in r.attrib]
   self.assertAlmostEqual(values[0],cli.summary(self.s,self.refs)['metrics']['strict_prompt']['full_accuracy']*100,8)
   self.assertEqual(values[1:],[r['value'] for r in x['rows']])
   for r in x['rows']:
    self.assertIn(r['snapshot'],texts)
    self.assertIn(f"External · {r['reporting_organization']} · {r['evaluation_date'] or 'date unknown'}",texts)
    self.assertIn('Sources: '+r['source_title'],texts)
   self.assertIn('IFEval strict prompt-level accuracy',texts)
   self.assertIn('0%',texts);self.assertIn('100%',texts)
 def test_report_description(self):
  with tempfile.TemporaryDirectory() as d:
   cli.do_report(self.r,self.r/'results/v0.1/scores.json',Path(d)/'real')
   cli.do_report(self.r,self.r/'examples/verdicts.json',Path(d)/'example',self.r/'examples/coverage.json')
   self.assertIn('Report aggregated from stored benchmark verdicts',(Path(d)/'real/scorecard.md').read_text())
   self.assertIn('Synthetic stored-verdict usage example; not benchmark measurement',(Path(d)/'example/scorecard.md').read_text())
if __name__=='__main__':unittest.main()
