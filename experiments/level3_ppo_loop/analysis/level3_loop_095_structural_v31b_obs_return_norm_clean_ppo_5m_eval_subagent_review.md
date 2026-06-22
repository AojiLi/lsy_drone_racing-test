# Loop095 v31b Evaluator Metrics Review

## Key Finding

Reject `v31b_obs_return_norm_clean_ppo_5m` for maturation. On hard eval with
`config/level3.toml` / `validation_unseen`, every loop095 checkpoint has
`0/100` successes. Gate progress is essentially absent: `mean_gates=0.00`
through 4M and only `0.01` at final.

## Evidence

| Checkpoint | Success | Crash | Timeout | Mean Gates | Mean Success Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop095 1M | 0% | 96% | 4% | 0.00 | n/a |
| loop095 2M | 0% | 96% | 4% | 0.00 | n/a |
| loop095 3M | 0% | 99% | 1% | 0.00 | n/a |
| loop095 4M | 0% | 100% | 0% | 0.00 | n/a |
| loop095 final | 0% | 99% | 1% | 0.01 | n/a |

Failure target-gate evidence is severe: `failures_by_target_gate={"0": 100}`
for 1M-4M, and only the final checkpoint moves one episode to gate 1.

## Comparison

Loop094/v31a best hard-eval checkpoint is 4M: `19/100` success, `81%` crash,
`mean_gates=1.55`, `mean_success_time=6.876s`.

The validation-unseen frontier anchor still records loop052 final at `20/100`
success, `80%` crash, `mean_gates=1.47`, `mean_success_time=6.858s`. Loop095 is
far below both: `-19pp` versus active best and `-20pp` versus the frontier
anchor.

## Diagnostic

The evaluator action/tilt fields suggest under-actuated behavior rather than a
promising immature policy: loop095 action deltas are `0.026-0.078` and
command-tilt over-limit fraction is near zero, while loop094 runs around
`0.333-0.343` action delta and `0.32-0.39` command-tilt over-limit fraction.
Before retrying normalization, run a focused observation/return-normalization
eval-path and action-scale diagnostic against loop094 on the same seeds.

## Recommendation

Decision: `launch_named_structural_lane` or `hold_for_more_analysis`, not
`continue_same_hypothesis`.

Do not mature loop095/v31b to 30M/60M. Treat this screen as a regression and
preserve loop094/v31a as the active best.
