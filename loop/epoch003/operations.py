"""Two consumers of the same CHIA worker, sampler, lease and planner contracts."""
import hashlib
import numpy as np
import torch
import triton
import triton.language as tl

@triton.jit
def row_sum(X,Y,N:tl.constexpr,BLOCK:tl.constexpr):
    row=tl.program_id(0)
    j=tl.arange(0,BLOCK)
    x=tl.load(X+row*N+j,j<N,other=0)
    tl.store(Y+row,tl.sum(x,0))

def reduction_base(x,out,scratch):
    torch.sum(x,dim=1,out=out)
    return out

def reduction_fused(x,out,scratch):
    row_sum[(x.shape[0],)](x,out,x.shape[1],BLOCK=triton.next_power_of_2(x.shape[1]))
    return out

def reduction_oracle(fn,n):
    # Binary fractions, exact sum within float32 range; every output checked in CPU float64.
    a=((np.arange(128*n,dtype=np.int64)%31)-15).astype(np.float32).reshape(128,n)/16
    x=torch.from_numpy(a).cuda();out=torch.empty(128,device='cuda');scratch=torch.empty_like(out)
    expected=a.astype(np.float64).sum(1).astype(np.float32)
    fn(x,out,scratch);torch.cuda.synchronize()
    if not np.array_equal(out.cpu().numpy(),expected):raise AssertionError('reduction CPU oracle mismatch')
    for k in [1,31,129]:
        aa=a[:,:min(k,n)].copy();xx=torch.from_numpy(aa).cuda();oo=torch.empty_like(out)
        fn(xx,oo,scratch);torch.cuda.synchronize()
        if not np.array_equal(oo.cpu().numpy(),aa.astype(np.float64).sum(1).astype(np.float32)):raise AssertionError('reduction tail oracle mismatch')
    return x,out,scratch,{'status':'PASS','rows':128,'columns':n,'input_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'oracle_sha256':hashlib.sha256(expected.tobytes()).hexdigest()}

def setup(path,implementation,baseline,correctness):
    if path=='reduction':
        base=reduction_base;selected=reduction_fused;oracle=reduction_oracle
        if implementation=='v2':
            def selected(x,out,scratch):
                reduction_fused(x,out,scratch)
                return reduction_fused(x,out,scratch)
    else:
        base=baseline;oracle=correctness
        from challenger import operation as selected
        if implementation=='v2':
            from challenger_v2 import operation as selected
            def resolved(x,out,scratch):return selected(x,out,scratch)
            # Worker resolves small-vector identity outside the timed call path below.
    if implementation=='slow':
        def selected(x,out,scratch):
            base(x,out,scratch)
            return base(x,out,scratch)
    return base,selected,oracle
