# POST-HELDOUT MECHANISM ATLAS — PUBLIC-SAFE SUMMARY

State: `EXPLORATORY / POST_HELDOUT / DOES_NOT_REWRITE_C_128`

```yaml
synthetic_replay_scenarios: 1200000
grid_rows: 37337
decision_error_rate: 0.0
FULL_A_ge10pct_advantage_rate_synthetic: 0.44123666666666667
B3_ge10pct_advantage_rate_synthetic: 0.0373975
collapse_rate_synthetic: 0.3998683333333333

H100_frontier:
  frozen_cases: 12
  resolved_cases: 12
  physical_live_cells: 26
  region_fidelity: 1.0
  decision_sound_rate: 1.0
  observed_regions:
    FULL_A_ADVANTAGE: 7
    B3_ADVANTAGE: 2
    COLLAPSE: 2
    NEAR_TIE: 1

temporal_spot_check:
  separation_seconds: 1800
  round2_cells: 4

claim_boundary:
  NO_PROMOTION: true
  champion: C_035
  frozen_G2_G3: IMMUTABLE
  universal_FULL_A_superiority: NOT_SUPPORTED
```

The 1.2M rates are synthetic/replay frequencies, not real-world prevalence estimates.
The 12 selected H100 cases validate mechanism-region predictions, not population frequency.
