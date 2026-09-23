"""Deterministic oracle and raw CUDA-event sampler. Invoked by a real CHIA node."""
import argparse, datetime, hashlib, json, os, pathlib, subprocess, threading, time
import numpy as np
import torch
from baseline import operation as baseline
from operations import setup


def query():
    p = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10)
    if p.returncode: raise RuntimeError('GPU process query failed')
    rows = [r.strip() for r in p.stdout.splitlines() if r.strip()]
    return {'time_ns': time.time_ns(), 'rows': rows,
            'unexpected': [r for r in rows if int(r.split(',')[0]) != os.getpid()]}


def correctness(fn, n):
    # Every measured element is checked independently on CPU in float64.
    a = ((np.arange(n, dtype=np.int64) % 2048) - 1024).astype(np.float32) / 128
    x = torch.from_numpy(a).cuda(); out = torch.empty_like(x); scratch = torch.empty_like(x)
    expect = np.maximum(a.astype(np.float64)*0.5 + 0.25, 0).astype(np.float32)
    fn(x, out, scratch); torch.cuda.synchronize()
    actual = out.cpu().numpy()
    if not np.array_equal(actual, expect): raise AssertionError('full vector oracle mismatch')
    checks = []
    for length in [1, 31, 1023, 1025, 4099]:
        rng = np.random.default_rng(32+length)
        b = rng.uniform(-16, 16, length).astype(np.float32)
        b[:min(length,5)] = np.array([-0.5,0,0.5,-1,1], dtype=np.float32)[:min(length,5)]
        xx=torch.from_numpy(b).cuda(); oo=torch.empty_like(xx); ss=torch.empty_like(xx)
        fn(xx,oo,ss); torch.cuda.synchronize()
        expected=np.maximum(b.astype(np.float64)*0.5+0.25,0).astype(np.float32)
        if not np.array_equal(oo.cpu().numpy(),expected): raise AssertionError('boundary oracle mismatch')
        checks.append(length)
    return x,out,scratch,{'status':'PASS','full_elements':n,'boundary_lengths':checks,'input_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'oracle_sha256':hashlib.sha256(expect.tobytes()).hexdigest()}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--path',default='affine');ap.add_argument('--implementation',default='v1');ap.add_argument('--batch',type=int,default=100);ap.add_argument('--n',type=int,required=True);ap.add_argument('--variant',choices=['baseline','candidate'],required=True);ap.add_argument('--samples',type=int,default=31);ap.add_argument('--output',required=True);args=ap.parse_args()
    global baseline, correctness
    baseline, selected_override, correctness = setup(args.path,args.implementation,baseline,correctness)
    dest=pathlib.Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    result={'n':args.n,'variant':args.variant,'pid':os.getpid(),'samples':[],'telemetry':[],'status':'RUNNING','batch_calls':args.batch,'warmup_calls':30,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    stop=threading.Event()
    def monitor():
        while not stop.is_set():
            try: result['telemetry'].append(query())
            except Exception as e:result['telemetry'].append({'error':str(e),'unexpected':['monitor_failure']})
            stop.wait(0.1)
    t=None
    try:
        first=query();result['telemetry'].append(first)
        if first['unexpected']:raise RuntimeError('unexpected GPU process before run')
        assert torch.cuda.is_available()
        result['gpu']=torch.cuda.get_device_name();assert 'H100' in result['gpu']
        result['torch']=torch.__version__;result['cuda']=torch.version.cuda
        t=threading.Thread(target=monitor,daemon=True);t.start()
        if args.path=='reduction' or args.implementation!='v1':
            selected=selected_override
        elif args.variant=='candidate':
            from challenger import operation as selected
            # Resolve unchanged baseline once, outside the measured call path.
            if args.n < 1048576: selected=baseline
        else:selected=baseline
        if args.path=='affine' and args.implementation=='v2' and args.n<1048576:selected=baseline
        x,out,scratch,oracle=correctness(selected,args.n);result['oracle']=oracle
        # Baseline correctness separately, with the same deterministic contract.
        bx,bo,bs,baseline_oracle=correctness(baseline,args.n);result['baseline_oracle']=baseline_oracle
        if args.variant=='candidate' and args.path=='affine':
            from challenger import fused
            _,_,_,result['forced_fused_tail_oracle']=correctness(fused,4099)
        functions={'baseline':lambda:baseline(bx,bo,bs),'selected':lambda:selected(x,out,scratch)}
        warm_start=time.perf_counter()
        for fn in functions.values():
            for _ in range(30):fn()
        torch.cuda.synchronize();result['warmup_seconds']=time.perf_counter()-warm_start
        for i in range(args.samples):
            row={'index':i,'order':['baseline','selected'] if i%2==0 else ['selected','baseline']}
            for label in row['order']:
                torch.cuda.synchronize();start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
                wall=time.perf_counter();start.record()
                for _ in range(args.batch):functions[label]()
                end.record();end.synchronize()
                row[label+'_ms']=start.elapsed_time(end)/args.batch
                row[label+'_wall_ms']=(time.perf_counter()-wall)*1000/args.batch
            result['samples'].append(row)
        result['telemetry'].append(query())
        if any(r.get('unexpected') for r in result['telemetry']):raise RuntimeError('GPU contamination observed; entire cell quarantined')
        result['baseline_median_ms']=float(np.median([s['baseline_ms'] for s in result['samples']]))
        result['selected_median_ms']=float(np.median([s['selected_ms'] for s in result['samples']]))
        result['speedup']=result['baseline_median_ms']/result['selected_median_ms']
        result['status']='PASS'
    except Exception as e:
        result['status']='QUARANTINED';result['error']=repr(e)
    finally:
        stop.set()
        if t:t.join(timeout=15)
        if any(r.get('unexpected') for r in result['telemetry']):
            result['status']='QUARANTINED';result['error']='unexpected GPU process or failed monitor'
        result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        dest.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['samples','telemetry']}))
    if result['status']!='PASS':raise SystemExit(2)
if __name__=='__main__':main()
