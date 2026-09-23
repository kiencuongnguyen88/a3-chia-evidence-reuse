import unittest,itertools
from planner import Scope,cache_key,evaluate,can_stop
class PlannerTests(unittest.TestCase):
    def test_early_rejection_cannot_hide_a_promotion(self):
        weights={1:1,2:2,3:0}
        for seq in itertools.product([.5,.949,1,1.15,4],repeat=3):
            full=dict(zip(weights,seq))
            for mask in itertools.product([False,True],repeat=3):
                partial={n:full[n] for n,m in zip(weights,mask) if m}
                if can_stop('FULL_A',partial,weights):self.assertEqual(evaluate(full,weights),'REJECT')
    def test_unknown_never_promotes(self):
        self.assertEqual(evaluate({1:100},{1:1,2:1}),'UNRESOLVED')
    def test_typed_dependencies_invalidate(self):
        a=Scope('affine',4096,'float32','contiguous','a','env','eval','oracle')
        import dataclasses
        for field,value in [('code','b'),('environment','changed'),('evaluator','changed'),('shape',8192),('dtype','float16'),('layout','strided'),('oracle','changed')]:
            b=dataclasses.replace(a,**{field:value})
            self.assertNotEqual(cache_key('FULL_A',a,'bundle','protocol'),cache_key('FULL_A',b,'bundle','protocol'))
    def test_presentation_and_weight_changes_do_not_invalidate_raw(self):
        a=Scope('affine',4096,'float32','contiguous','a','env','eval','oracle')
        for method in ['B2','B3','FULL_A']:
            self.assertEqual(cache_key(method,a,'bundle','old'),cache_key(method,a,'bundle','new'))
        self.assertNotEqual(cache_key('B1',a,'bundle','old'),cache_key('B1',a,'bundle','new'))
    def test_bundle_scope_ablation(self):
        a=Scope('affine',4096,'float32','contiguous','a','env','eval','oracle')
        self.assertEqual(cache_key('FULL_A',a,'old','p'),cache_key('FULL_A',a,'new','p'))
        self.assertNotEqual(cache_key('B2',a,'old','p'),cache_key('B2',a,'new','p'))
if __name__=='__main__':unittest.main()
