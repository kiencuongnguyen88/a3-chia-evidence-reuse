"""Same-target fusion for large vectors. Small-vector incumbent is unchanged."""
import triton
import triton.language as tl
from baseline import operation as baseline

@triton.jit
def affine_relu(X, Y, N: tl.constexpr, BLOCK: tl.constexpr):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    x = tl.load(X + offsets, mask=offsets < N, other=0.0)
    y = tl.maximum(x * 0.5 + 0.25, 0.0)
    tl.store(Y + offsets, y, mask=offsets < N)

def fused(x, out, scratch):
    n=x.numel()
    affine_relu[(triton.cdiv(n, 1024),)](x,out,n,BLOCK=1024,enable_fp_fusion=False)
    return out

def operation(x, out, scratch):
    if x.numel() < 1048576:
        return baseline(x, out, scratch)
    return fused(x,out,scratch)
