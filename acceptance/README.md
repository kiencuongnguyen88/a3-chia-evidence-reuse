# PUBLIC FULL-LOOP ACCEPTANCE

This directory is orchestration glue added after the science mainline closed.

It exercises existing public planner/oracle semantics in three bounded cases:

1. valid typed evidence reuse with zero new H100 measurement;
2. changed environment scope invalidates historical evidence and forces a live H100 measurement;
3. no compatible prior makes B3 and FULL_A choose the same measurement order and final decision.

A public one-cell H100 run is only a GPU smoke. `FULL_LOOP_ACCEPTANCE.json` is the stronger acceptance receipt.

This acceptance does not modify frozen G2/G3, does not promote FULL_A, and is not a new science experiment.
