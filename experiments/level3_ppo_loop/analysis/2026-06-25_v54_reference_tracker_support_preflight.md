# V54 Reference Tracker PPO Support Preflight

Created: 2026-06-25

Lane: `v54_reference_trajectory_tracker_ppo`

Target remains unchanged: hard evaluation must use `config/level3.toml`.

## What Changed

This preflight implements the support layer for a native reference-tracking PPO
controller:

- `lsy_drone_racing/control/level3_reference_tracker.py`
  - reference trajectory generator for `hover`, `point`, `gate_aperture`, and
    deployed `level3` tracking;
  - 65-dimensional tracker observation;
  - dense tracker reward;
  - 2x256 Tanh `TrackerPPOAgent`;
  - single-env `ReferenceTrackerEnv`;
  - checkpoint save/load and action scaling helpers.
- `lsy_drone_racing/control/train_level3_reference_tracker_ppo.py`
  - narrow PPO training entrypoint for the v54 tracker tasks;
  - optional W&B logging;
  - metadata-rich v54 checkpoint output.
- `lsy_drone_racing/control/level3_reference_tracker_controller.py`
  - deployed Level3 controller path:
    reference generator -> tracker observation -> `TrackerPPOAgent` ->
    roll/pitch/yaw/thrust;
  - the planner/reference module does not output actions;
  - no track changes, seed replay, shield, MPC, or planner action override.
- `scripts/check_level3_reference_tracker_smoke.py`
  - smoke tests for native tracker tasks and Level3 seeds `101-105`;
  - separates `all_finite` from `long_training_gate_passed`.

## Smoke Result

Smoke report:
`experiments/level3_ppo_loop/analysis/2026-06-25_v54_reference_tracker_smoke.json`

Command:

```bash
pixi run -e gpu python scripts/check_level3_reference_tracker_smoke.py \
  --allow-untrained \
  --task-steps 80 \
  --level3-steps 150 \
  --level3-seeds 101-105 \
  --output experiments/level3_ppo_loop/analysis/2026-06-25_v54_reference_tracker_smoke.json
```

Key result:

- `all_finite`: `true`;
- `checkpoint_backed`: `false`;
- `any_nonzero_first_gate_progress`: `true`;
- `long_training_gate_passed`: `false`;
- `promotion_ready_for_long_training`: `false`.

Interpretation: the support path is action-finite and can run through the
unchanged Level3 simulator, but this was an untrained-network smoke. The small
first-gate axis gains are only a wiring/finite-action sanity signal, not a
behavioral training gate.

## Local Checks

Passed:

```bash
git diff --check -- \
  lsy_drone_racing/control/level3_reference_tracker.py \
  lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  lsy_drone_racing/control/level3_reference_tracker_controller.py \
  scripts/check_level3_reference_tracker_smoke.py

pixi run -e gpu python -m py_compile \
  lsy_drone_racing/control/level3_reference_tracker.py \
  lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  lsy_drone_racing/control/level3_reference_tracker_controller.py \
  scripts/check_level3_reference_tracker_smoke.py

pixi run -e gpu ruff check \
  lsy_drone_racing/control/level3_reference_tracker.py \
  lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  lsy_drone_racing/control/level3_reference_tracker_controller.py \
  scripts/check_level3_reference_tracker_smoke.py

pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run
```

The dry run remains held by the existing state guard, which is expected for the
old orchestrator path. v54 support did not launch training.

## Decision

Do not launch long training yet.

Next action should be a bounded tracker curriculum check:

1. Train a small v54 tracker checkpoint on `hover`, `point`, then
   `gate_aperture`.
2. Run the checkpoint-backed smoke on Level3 seeds `101-105`.
3. Launch longer W&B-tracked tracker training only if checkpoint-backed smoke
   has finite actions and nonzero first-gate progress.

The global PPO best remains unchanged:

- checkpoint: `level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight:1M`;
- success: `21%`;
- mean gates: `1.66`;
- crash: `79%`;
- mean successful time: `7.578s`;
- target met: `false`.
