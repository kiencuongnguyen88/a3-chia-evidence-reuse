"""Incumbent operation; workspace-owned benchmark, no upstream modifications."""
def operation(x, out, scratch):
    import torch
    torch.mul(x, 0.5, out=scratch)
    torch.add(scratch, 0.25, out=out)
    out.clamp_(min=0.0)
    return out
