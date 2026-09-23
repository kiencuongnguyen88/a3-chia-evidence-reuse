# Frozen held-out G2/G3 summary

Final acceptance: **NO_PROMOTION**.

| Method | Cells | Sampled GPU s | Wall s |
|---|---:|---:|---:|
| B0 | 7 | 2.010980 | 21.491598 |
| B3 | 5 | 1.777980 | 15.218925 |
| FULL_A | 5 | 1.782858 | 15.302370 |

G2: B0/B3/FULL_A all produce the frozen kernel-decision label `PROMOTE`, using 4/4/4 cells.  
G3: all produce `REJECT`; B0 uses 3 cells, while B3 and FULL_A each stop after 1.

The preregistered FULL_A material advantage over B3 fails on both live-cell and sampled-GPU-time criteria. Wall non-regression passes. `PROMOTE` inside G2 is only a per-case kernel decision label; it is not authorization to promote the planner or replace the champion.
