# V54 Reference Tracker Curriculum Preflight

Created: 2026-06-25

Lane: `v54_reference_trajectory_tracker_ppo`

Target config remains unchanged: `config/level3.toml`.

## Code Change

The v54 trainer now supports minimal checkpoint continuation:

- `--initial-model-path` loads an existing v54 tracker checkpoint;
- model weights are resumed with `load_tracker_checkpoint`;
- `global_step` starts from the prior checkpoint metadata;
- Adam optimizer state is not resumed, by design for this small curriculum
  preflight.

Checker result: `ALL GREEN`.

## Curriculum Run

This was a bounded preflight, not long training.

Final checkpoint:

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_curriculum_preflight/v54_reference_tracker_curriculum_gate_aperture.ckpt`

Checkpoint metadata:

- `global_step`: `24576`;
- `task`: `gate_aperture`;
- `config`: `level3.toml`;
- `observation_layout`: `level3_reference_tracker_v1`;
- `policy_arch`: `mlp_2x256_tanh`;
- `obs_dim`: `65`;
- `action_dim`: `4`;
- `hidden_dim`: `256`.

W&B runs:

- [hover](https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v54_tracker_curriculum_hover_20260625)
- [point](https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v54_tracker_curriculum_point_20260625)
- [gate_aperture](https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v54_tracker_curriculum_gate_aperture_20260625)

Each phase used `8192` tracker steps:

1. `hover`;
2. `point`, initialized from the hover checkpoint;
3. `gate_aperture`, initialized from the point checkpoint.

## Checkpoint-Backed Smoke

Smoke report:
`experiments/level3_ppo_loop/analysis/2026-06-25_v54_reference_tracker_checkpoint_backed_smoke.json`

Command:

```bash
pixi run -e gpu python scripts/check_level3_reference_tracker_smoke.py \
  --checkpoint lsy_drone_racing/control/checkpoints/v54_reference_tracker_curriculum_preflight/v54_reference_tracker_curriculum_gate_aperture.ckpt \
  --task-steps 80 \
  --level3-steps 150 \
  --level3-seeds 101-105 \
  --output experiments/level3_ppo_loop/analysis/2026-06-25_v54_reference_tracker_checkpoint_backed_smoke.json
```

Result:

- `all_finite`: `true`;
- `checkpoint_backed`: `true`;
- `long_training_gate_passed`: `true`;
- `promotion_ready_for_long_training`: `true`;
- Level3 seeds: `101-105`.

Per-seed Level3 smoke:

| seed | steps | terminated | first-gate axis gain | nonzero progress | max gate index |
| --- | ---: | --- | ---: | --- | ---: |
| 101 | 38 | true | 1.0848 | true | 0 |
| 102 | 31 | true | 0.0001 | false | 0 |
| 103 | 13 | true | 0.0007 | false | 0 |
| 104 | 23 | true | 0.1146 | true | 0 |
| 105 | 17 | true | 0.0195 | false | 0 |

## Interpretation

The formal preflight gate passed: the checkpoint-backed controller produces
finite actions and shows nonzero first-gate progress on two of five seeds.

However, this is not yet a healthy controller:

- all five Level3 smoke seeds terminate early;
- no seed passes gate 0;
- the checkpoint appears to create aggressive/unstable actions after only a
  tiny curriculum.

Therefore this preflight proves the pipeline, not the behavior. It is now
reasonable to continue v54 work, but the next run should still be a bounded
tracker-stability improvement, not a full overnight Level3 run.

## Recommended Next Action

Run a second bounded v54 tracker curriculum focused on stability before any long
Level3 training:

- increase hover and point curriculum length;
- lower learning rate or action aggressiveness if W&B shows action penalty and
  early termination remain high;
- add a checkpoint-backed smoke requirement that no more than two of five seeds
  terminate before `50` steps, in addition to finite action and nonzero
  first-gate progress.

Do not update the global Level3 `best`; this was not a hard validation run.
