# Structure/Research Synthesis Review: loop087

Verdict: hold the v27 beta sweep. Do not continue beta=0.10, do not try a
higher beta, and do not mature v27 to 60M.

Recommended main-agent action: `hold_for_more_analysis`.

## Rationale

The three-arm v27 screen is exhausted:

| Arm | Best validation success | Crash | Mean gates | Note |
| --- | ---: | ---: | ---: | --- |
| beta=0 | 0.10 | 0.90 | 1.38 | failed control |
| beta=0.03 | 0.14 | 0.86 | 1.55 | improved control, below anchor |
| beta=0.10 | 0.17 | 0.83 | 1.50 | best v27 success, still below anchor |

Loop052 anchor remains better: success 0.20, crash 0.80, mean gates 1.47.

Beta=0.10 shows the teacher-retention mechanism is active: sampled batches are
nonzero, teacher KL decreases, and tail teacher agreement is around 0.83, above
the 0.80 proxy. But the hard-eval gate did not restore anchor reliability:
validation success is still below 0.20, crash remains above 0.80, and failures
remain dominated by `bounds_or_ground`.

The v27 spec and loop086 stop rule both say to hold if beta=0.10 fails to
restore or exceed loop052. This is that case.

## Recommended Next Action

Write a hold decision packet, not a training command.

Use the hold to audit and improve the implementation/data path before any new
structural run:

- validate retention dataset metadata and seed exclusion;
- add analyzer summaries for retention metrics;
- add episode-level teacher-retention evaluation;
- build a larger or stratified train-pool retention/failure-correction dataset;
- keep `config/level3_dr.toml` unchanged;
- do not inspect or use `final_locked` seeds.

Suggested future lane name after the hold packet:
`v27_stratified_retention_failure_correction_data_audit`.

Reject the analyzer's generic gate-reward retune for the immediate next step;
it ignores the explicit v27 stop rule.
