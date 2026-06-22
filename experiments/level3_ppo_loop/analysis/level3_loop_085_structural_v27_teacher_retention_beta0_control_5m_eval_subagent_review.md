# Loop085 Evaluator-Metrics Review

Role: evaluator_metrics

Trial:
`level3_loop_085_structural_v27_teacher_retention_beta0_control_5m`

## Verdict

Reject and hold the beta=0 control arm. Do not continue or mature this branch.

The best validation checkpoint is 3M, but it reaches only 10% success on
`validation_unseen`, below the loop052 validation anchor.

## Key Metrics

Loop085 validation best, 3M:

- success: 10/100 = 0.10
- mean successful time: 6.97s
- crash: 0.90
- timeout: 0.00
- mean gates: 1.38
- success CI95: [0.055, 0.174]

Loop085 final:

- success: 8/100 = 0.08
- mean successful time: 9.567s
- crash: 0.92
- mean gates: 1.33

Loop052 validation anchor:

- success: 20/100 = 0.20
- mean successful time: 6.858s
- crash: 0.80
- mean gates: 1.47

## Delta Vs Anchor

Loop085 3M vs loop052 final:

- success: -10 percentage points
- mean successful time: +0.112s
- crash: +10 percentage points
- mean gates: -0.09

The loop085 validation CI high, 0.174, is below the loop052 point estimate,
0.20. This is not a promotion signal.

## Failure Pattern

Loop085 validation failures are dominated by `bounds_or_ground`:

- 3M: 90/100 `bounds_or_ground`
- final: 92/100 `bounds_or_ground`

Failures are concentrated before or around the first three gates:

- gate 0: 34%
- gate 1: 21%
- gate 2: 28%
- gate 3: 7%

This does not look like preserved loop052 behavior. It looks like short v8
continuation drifted into a more brittle crash mode.

## Recommendation

- Do not continue beta=0.
- Do not apply step-curve maturation to beta=0.
- Treat loop085 as a negative control: without real teacher retention, the
  short continuation does not preserve validation reliability.
- If v27 continues, it must use a real teacher-retention implementation and
  start with a named light nonzero-beta screen only after implementation review.
