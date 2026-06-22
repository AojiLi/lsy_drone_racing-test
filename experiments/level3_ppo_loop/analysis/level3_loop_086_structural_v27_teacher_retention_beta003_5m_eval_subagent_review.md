# Loop086 Evaluator-Metrics Review

Role: evaluator_metrics

Trial:
`level3_loop_086_structural_v27_teacher_retention_beta003_5m`

## Verdict

Do not continue or mature beta=0.03. Launch only one bounded beta=0.10 screen.

Beta=0.03 improved over the beta=0 control arm but did not beat the loop052
validation anchor.

## Key Metrics

Loop086 beta=0.03 validation best, 1M:

- success: 14/100 = 0.14
- crash: 0.86
- timeout: 0.00
- mean gates: 1.55
- mean successful time: 6.791s
- success CI95: [0.085, 0.221]

Dev best was also 1M:

- success: 4/20 = 0.20
- crash: 0.80
- mean gates: 2.10
- mean successful time: 7.31s

Later dev checkpoints regressed to 0.10-0.15 success, so the branch does not
support longer beta=0.03 maturation.

## Comparisons

Compared with loop052 validation anchor:

- loop052: 0.20 success, 0.80 crash, 1.47 mean gates, 6.858s
- loop086: -6pp success, +6pp crash, +0.08 mean gates, -0.067s

Compared with loop085 beta=0 validation best:

- loop085: 0.10 success, 0.90 crash, 1.38 mean gates, 6.97s
- loop086: +4pp success, -4pp crash, +0.17 mean gates, -0.179s

## Failure Taxonomy

Loop086 validation failures:

- endpoint classes: 86 `bounds_or_ground`, 14 success
- failures by target gate: gate0 31%, gate1 19%, gate2 28%, gate3 8%

Loop052 anchor is much less bounds/ground dominated and instead fails around
near-gate obstacle/frame classes. Beta=0.03 pushes some failures later than
beta=0, but it does not recover loop052-style reliability.

## Recommendation

Run `v27_teacher_retention_beta010_5m` as the final medium-strength v27 KL
screen. Do not mature beta=0.03 to 60M or 90M.

The beta=0.10 gate should be strict:

- validation success should reach at least 0.20;
- crash should be at or below 0.80;
- bounds/ground taxonomy should improve materially.
