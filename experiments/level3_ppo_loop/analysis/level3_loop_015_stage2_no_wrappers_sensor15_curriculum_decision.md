# Level3 Loop 015 Decision: Reject No-Wrappers + Sensor15 Curriculum

## Decision

Reject `level3_loop_015_stage2_no_wrappers_sensor15_curriculum`.

Do not continue this branch and do not treat the easier training sensor range as
progress on the competition task.

The hard evaluator remained the original target:

```text
config/level3_dr.toml
```

That hard evaluator did not improve over the current incumbent.

## User Constraint

The Level3 race track is the hard competition target and must not be changed for
the score. This run only changed the training curriculum, not the hard
evaluator. Its only valid purpose was to see whether a controller checkpoint
trained with easier first-gate visibility could transfer back to the original
Level3 hard evaluator.

It did not transfer.

## Hard Evaluator Evidence

Current global incumbent:

```text
lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt
```

Incumbent metrics:

```text
success_rate = 0.05
mean_time_s_success = 5.64
mean_gates = 0.80
crash_rate = 0.95
```

Loop015 best checkpoint under hard eval:

```text
lsy_drone_racing/control/checkpoints/level3_loop_015_stage2_no_wrappers_sensor15_curriculum/level3_loop_015_stage2_no_wrappers_sensor15_curriculum_step_015000000.ckpt
```

Loop015 best metrics:

```text
success_rate = 0.00
mean_time_s_success = null
mean_gates = 0.90
crash_rate = 1.00
timeout_rate = 0.00
```

Checkpoint sweep:

| Checkpoint | Success | Mean gates | Crash | Timeout |
| --- | ---: | ---: | ---: | ---: |
| 5M | `0.00` | `0.75` | `1.00` | `0.00` |
| 10M | `0.00` | `0.65` | `1.00` | `0.00` |
| 15M | `0.00` | `0.90` | `1.00` | `0.00` |
| 20M | `0.00` | `0.70` | `1.00` | `0.00` |
| 25M | `0.00` | `0.65` | `1.00` | `0.00` |
| final | `0.00` | `0.65` | `1.00` | `0.00` |

## W&B Evidence

Run:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_015_stage2_no_wrappers_sensor15_curriculum
```

Relevant post-run analyzer signals:

```text
race/passed_gate_rate tail_mean = 0.010941, flat
race/finished_rate tail_mean = 0.000031, flat
losses/approx_kl tail_mean = 0.002056, flat
losses/clipfrac tail_mean = 0.000974, flat
```

Interpretation:

- PPO did not blow up.
- Training reward improved somewhat, but hard evaluator success stayed zero.
- The curriculum did not create reliable gate/finish conversion on the real
  Level3 target.

## What This Means

The experiment answered a useful question:

```text
Does easier first-gate visibility during training produce a controller that
transfers back to original level3_dr.toml?
```

Answer:

```text
No, not in this 30M continuation from loop010.
```

This makes the user's concern stronger: changing training visibility can create
a different learning problem without improving the real competition controller.

## Next Rule

Do not launch another training run automatically.

If the user wants all future work to keep even the training config identical to
`level3_dr.toml`, then future Stage 2 must focus on controller-side changes
only, such as:

- controller observation processing that is valid under original observations;
- checkpoint selection / longer training on the original `level3_dr.toml`;
- reward numbers only under original `level3_dr.toml`;
- code-level controller robustness fixes that do not change the race track or
  hard evaluator.

No next training command is approved by this decision.
