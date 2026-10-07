from __future__ import annotations
import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[1]; sys.path.insert(0,str(HERE))
from validity_inferencer import *
LOOP=REPO/'loop'/'epoch002'
BASELINE=(LOOP/'baseline.py').read_text(); V1=(LOOP/'challenger.py').read_text(); V2=(LOOP/'challenger_v2.py').read_text(); OPS=(LOOP/'operations.py').read_text()
EXP=json.loads((HERE/'R1_REPLAY_EXPECTATIONS.json').read_text())
AFF=[4096,262144,1048576,16777216]; RED=[128,1024,4096]; G=GlobalDeps('env1','eval1','oracle1')
def ids(r): return reusable_ids(r),invalid_ids(r)
class IntegrationTests(unittest.TestCase):
 def test_affine_presentation(self):
  self.assertEqual(ids(compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,V1,AFF,G))),(EXP['affine']['presentation']['reusable'],EXP['affine']['presentation']['invalid']))
 def test_affine_kernel_v2(self):
  self.assertEqual(ids(compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,V2,AFF,G))),(EXP['affine']['kernel_v2']['reusable'],EXP['affine']['kernel_v2']['invalid']))
 def test_affine_evaluator(self):
  r=compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,V1,AFF,GlobalDeps('env1','eval2','oracle1'))); self.assertEqual(len(invalid_ids(r)),4)
 def test_affine_environment(self):
  r=compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,V1,AFF,GlobalDeps('env2','eval1','oracle1'))); self.assertEqual(len(invalid_ids(r)),4)
 def test_affine_oracle(self):
  r=compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,V1,AFF,GlobalDeps('env1','eval1','oracle2'))); self.assertEqual(len(invalid_ids(r)),4)
 def test_affine_dtype(self):
  old=affine_snapshots(BASELINE,V1,[TypedScope(n) for n in AFF],G); new=affine_snapshots(BASELINE,V1,[TypedScope(n,'float16','contiguous') for n in AFF],G); self.assertEqual(len(invalid_ids(compare(old,new))),4)
 def test_affine_layout(self):
  old=affine_snapshots(BASELINE,V1,[TypedScope(n) for n in AFF],G); new=affine_snapshots(BASELINE,V1,[TypedScope(n,'float32','strided') for n in AFF],G); self.assertEqual(len(invalid_ids(compare(old,new))),4)
 def test_affine_added_scope(self):
  r=compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,V1,AFF+[2097152],G)); self.assertEqual(reusable_ids(r),[str(x) for x in AFF]); self.assertIn('2097152',invalid_ids(r))
 def test_affine_removed_scope(self):
  r=compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,V1,AFF[:-1],G)); self.assertIn('16777216',invalid_ids(r))
 def test_affine_baseline_change_invalidates_all(self):
  changed=BASELINE.replace('0.5','0.6',1); r=compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(changed,V1,AFF,G)); self.assertEqual(len(invalid_ids(r)),4)
 def test_affine_import_retarget_invalidates_all(self):
  changed=V1.replace('from baseline import operation as baseline','from challenger_v2 import operation as baseline'); r=compare(affine_snapshots(BASELINE,V1,AFF,G),affine_snapshots(BASELINE,changed,AFF,G)); self.assertEqual(len(invalid_ids(r)),4)
 def test_affine_ambiguous_dispatch_fails_closed(self):
  changed=V1.replace('if x.numel() < 1048576:','if x.numel() < 1048576 and x.numel() < 2097152:'); r=infer_or_fail_closed(affine_snapshots,BASELINE,changed,AFF,G); self.assertTrue(r.fail_closed)
 def test_reduction_presentation(self):
  self.assertEqual(ids(compare(reduction_snapshots(OPS,RED,'v1',G),reduction_snapshots(OPS,RED,'v1',G))),(EXP['reduction']['presentation']['reusable'],EXP['reduction']['presentation']['invalid']))
 def test_reduction_v2(self):
  self.assertEqual(ids(compare(reduction_snapshots(OPS,RED,'v1',G),reduction_snapshots(OPS,RED,'v2',G))),(EXP['reduction']['kernel_v2']['reusable'],EXP['reduction']['kernel_v2']['invalid']))
 def test_reduction_evaluator(self):
  r=compare(reduction_snapshots(OPS,RED,'v1',G),reduction_snapshots(OPS,RED,'v1',GlobalDeps('env1','eval2','oracle1'))); self.assertEqual(len(invalid_ids(r)),3)
 def test_reduction_environment(self):
  r=compare(reduction_snapshots(OPS,RED,'v1',G),reduction_snapshots(OPS,RED,'v1',GlobalDeps('env2','eval1','oracle1'))); self.assertEqual(len(invalid_ids(r)),3)
 def test_reduction_dtype(self):
  old=reduction_snapshots(OPS,[TypedScope(n) for n in RED],'v1',G); new=reduction_snapshots(OPS,[TypedScope(n,'float16','contiguous') for n in RED],'v1',G); self.assertEqual(len(invalid_ids(compare(old,new))),3)
 def test_reduction_layout(self):
  old=reduction_snapshots(OPS,[TypedScope(n) for n in RED],'v1',G); new=reduction_snapshots(OPS,[TypedScope(n,'float32','strided') for n in RED],'v1',G); self.assertEqual(len(invalid_ids(compare(old,new))),3)
 def test_reduction_setup_mutation_invalidates_all(self):
  changed=OPS.replace("base=reduction_base;selected=reduction_fused;oracle=reduction_oracle","base=reduction_base;selected=reduction_base;oracle=reduction_oracle"); r=compare(reduction_snapshots(OPS,RED,'v1',G),reduction_snapshots(changed,RED,'v1',G)); self.assertEqual(len(invalid_ids(r)),3)
 def test_reduction_baseline_mutation_invalidates_all(self):
  changed=OPS.replace('torch.sum(x,dim=1,out=out)','torch.sum(x,dim=1,out=out)\n    out.add_(1.0)'); r=compare(reduction_snapshots(OPS,RED,'v1',G),reduction_snapshots(changed,RED,'v1',G)); self.assertEqual(len(invalid_ids(r)),3)
 def test_fail_closed_bad_affine(self):
  r=infer_or_fail_closed(affine_snapshots,BASELINE,'def nope(:',AFF,G); self.assertTrue(r.fail_closed); self.assertEqual(tuple(),r.decisions)
 def test_fail_closed_bad_reduction_impl(self):
  r=infer_or_fail_closed(reduction_snapshots,OPS,RED,'v9',G); self.assertTrue(r.fail_closed); self.assertEqual(tuple(),r.decisions)
if __name__=='__main__': unittest.main(verbosity=2)
