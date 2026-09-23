"""Offline ablations on already measured development traces; zero new GPU evidence."""
import pathlib,json,time,dataclasses
from run import R,D,identity,base_spec
from planner import Scope,Evidence,cache_key,choose,evaluate,can_stop

def main():
 out=[]
 for path in ['affine','reduction']:
  seed_json=json.loads((D/(path+'_typed_seed.json')).read_text())
  seed={int(n):Evidence(**{**v,'scope':Scope(**v['scope'])}) for n,v in seed_json.items()}
  prior={n:{'speedup':e.speedup,'cost':e.sampled_gpu_seconds} for n,e in seed.items()}
  for s in json.loads((D/(path+'_matrix.json')).read_text()):
   reference=json.loads((R/'evidence/baselines/B0'/path/s['id']/'result.json').read_text())
   raws={e['n']:e for e in reference['events']}
   weights={int(n):v for n,v in s['weights'].items()}
   for method in ['FULL_A_REPLAY','WITHOUT_TYPED_SCOPE','WITHOUT_SELECTOR']:
    begin=time.perf_counter();key_method='B2' if method=='WITHOUT_TYPED_SCOPE' else 'FULL_A'
    cache={cache_key(key_method,e.scope,e.candidate_bundle,identity(base_spec(path),n)[2]):e for n,e in seed.items()}
    values={};pending=list(s['sizes']);events=[]
    for n in list(pending):
     scope,bundle,proto=identity(s,n);key=cache_key(key_method,scope,bundle,proto)
     if key in cache:
      values[n]=cache[key].speedup;pending.remove(n);events.append({'n':n,'action':'historical_reuse','source':cache[key].raw_artifact,'counterfactual_gpu_seconds':0})
    while pending:
     if method!='WITHOUT_SELECTOR':
      if can_stop('FULL_A',values,weights):break
      active=[n for n in pending if weights[n]>0]
      if not active:break
      n=choose('FULL_A',active,weights,prior)
     else:n=min(pending)
     e=raws[n];values[n]=e['record']['speedup'];pending.remove(n)
     events.append({'n':n,'action':'replay_B0_measurement','source':e['record']['raw_artifact'],'counterfactual_gpu_seconds':e['new_gpu_seconds']})
    dec=evaluate(values,weights);assert dec!='UNRESOLVED'
    out.append({'path':path,'scenario':s['id'],'method':method,'live_vs_replay':'replay_only','new_H100_measurements':0,'new_GPU_seconds':0,'replayed_measurement_demand':sum(e['action']=='replay_B0_measurement' for e in events),'counterfactual_sampled_gpu_seconds':sum(e['counterfactual_gpu_seconds'] for e in events),'planner_wall_seconds':time.perf_counter()-begin,'decision':dec,'agreement':dec==reference['decision'],'events':events,'skipped':pending})
 (D/'ablations.json').write_text(json.dumps(out,indent=2))
 print(json.dumps({'replay_comparisons':len(out),'decision_errors':sum(not x['agreement'] for x in out),'new_GPU_seconds':0}))
if __name__=='__main__':main()
