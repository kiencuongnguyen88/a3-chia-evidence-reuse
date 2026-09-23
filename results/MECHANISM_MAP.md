# Conditional mechanism map

The richer FULL_A planner differs materially from B3 in development only where pre-existing evidence/decision structure gives it something additional to exploit:

1. **Affine kernel change:** callable-scope validity allows unchanged small-vector behavior to reuse evidence while changed large-vector behavior is remeasured.
2. **Affine regressing kernel:** prior cost/risk information changes which rejection witness is measured first.
3. **Affine inactive added shape:** a zero-weight shape is outside the active decision scope and can be omitted.

Frozen G2/G3 deliberately lacks these enabling signals: all shapes are unseen, no compatible history or shape-indexed ranking prior exists, and all weights are positive. FULL_A therefore collapses to B3’s effective plan.

This pattern supports a conditional mechanism; it does not establish global FULL_A superiority.
