#!/usr/bin/env python3
import json, pathlib, math
p=pathlib.Path(__file__).parent/'results'/'RESULTS_SUMMARY.json'
d=json.loads(p.read_text())
dev=d['development']; h=d['heldout']; b3=h['aggregate']['B3']; fa=h['aggregate']['FULL_A']
assert dev['B3']['decision_errors']==0 and dev['FULL_A']['decision_errors']==0
assert dev['B3']['missed_useful_candidates']==0 and dev['FULL_A']['missed_useful_candidates']==0
assert dev['FULL_A']['live_cells']==11 and dev['B3']['live_cells']==14
assert h['G2']['B3']['cells']==h['G2']['FULL_A']['cells']==4
assert h['G3']['B3']['cells']==h['G3']['FULL_A']['cells']==1
assert not (fa['cells'] <= .90*b3['cells'])
assert not (fa['sampled_gpu_seconds'] <= .90*b3['sampled_gpu_seconds'])
assert fa['wall_seconds'] <= 1.05*b3['wall_seconds']
assert h['acceptance']=='NO_PROMOTION'
print('PUBLIC_EVIDENCE_REPLAY=PASS')
print('development_FULL_A_vs_B3_cells=11_vs_14')
print(f"heldout_FULL_A_vs_B3_cells={fa['cells']}_vs_{b3['cells']}")
print(f"heldout_FULL_A_vs_B3_gpu_s={fa['sampled_gpu_seconds']:.6f}_vs_{b3['sampled_gpu_seconds']:.6f}")
print('acceptance=NO_PROMOTION')
