# V52 MPPI Oracle Smoke Preflight Analysis

Date: 2026-06-25

Lane: `v52_mppi_oracle_teacher_level3`

Controller: `lsy_drone_racing/control/mppi_level3_oracle.py`

Evaluator: `scripts/evaluate_level3_controller.py`

Target config: unchanged `config/level3.toml`

## Summary

This preflight implemented the first MPPI-only Level3 controller/evaluator loop.
It does not use PPO, BC, DAgger, imitation learning, teacher data generation, or
PPO fine-tuning. MPPI success here is controller/oracle evidence only and is not
recorded as PPO success.

Current smoke result on seeds `101-105`:

- success: `0/5` = `0%`;
- mean gates: `0.80`;
- crash: `5/5` = `100%`;
- timeout: `0/5` = `0%`;
- finite action rate: `100%`;
- mean successful time: `nan` because there were no successful episodes;
- termination reasons: `{"contact": 5}`;
- best observed single-seed progress: seed `103` reached gate index `2`.

The current PPO frontier remains unchanged:

- success: `21%`;
- mean gates: `1.66`;
- crash: `79%`;
- mean successful time: `7.578s`;
- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt`.

## Implementation Evidence

Added:

- `lsy_drone_racing/control/mppi_level3_oracle.py`
  - MPPI-only controller returning `[roll, pitch, yaw, thrust]`;
  - finite action clipping and normalized action diagnostics;
  - warm-started action sequence sampling;
  - gate progress, aperture, obstacle, bounds, tilt, smoothness, and finish
    scoring with a simplified rollout model.
- `scripts/evaluate_level3_controller.py`
  - non-PPO controller evaluator;
  - seed/range parsing;
  - success, crash, timeout, mean gates, time, smoothness, tilt, termination
    reason, endpoint taxonomy, and finite-action metrics.

Checker result: `ALL GREEN`.

Checker evidence included:

- `git diff --check`: passed;
- Python compile checks for touched files: passed;
- `config/level3.toml` unchanged;
- MPPI controller returns finite `[roll, pitch, yaw, thrust]`;
- evaluator records termination reasons and finite-action status;
- MPPI-only results were not recorded as PPO target success in `state.json`.

Local smoke command:

```bash
pixi run -e gpu python scripts/evaluate_level3_controller.py \
  --config level3.toml \
  --controller mppi_level3_oracle.py \
  --seed-start 101 \
  --num-seeds 5 \
  --seed-split-name smoke_101_105_v9_current \
  --failure-taxonomy \
  --out-prefix experiments/level3_ppo_loop/mppi/v52_mppi_level3_smoke_101_105_v9_current
```

Generated smoke CSVs are ignored artifacts and should not be committed.

## What Changed During Tuning

The first controller version returned finite actions but mostly fell or hit
bounds before useful gate progress.

The useful fixes were:

- add stronger centerline and altitude cost;
- add low-altitude thrust protection;
- identify that yaw-heavy commands made the simplified rollout model misleading;
- constrain yaw near zero so roll/pitch act more predictably in world x/y;
- replace the vertical guide with a PD-like vertical controller to reduce gate
  top/bottom overshoot.

The best smoke point so far is the current version:

- mean gates improved from `0.00` in the first smoke to `0.80`;
- finite-action and evaluator semantics are now clean;
- still no completed Level3 runs.

## Failure Analysis

All five smoke episodes still ended in contact. The evaluator taxonomy reports
`bounds_or_ground`, but short traces show that the useful failure mode is more
specific:

- the controller can approach and sometimes pass the first gate;
- some seeds collide around or shortly after gate transition;
- vertical speed and gate-plane timing are still not controlled well enough;
- obstacle-aware route quality has not yet been proven, because most failures
  happen before sustained multi-gate flight.

This is below the PPO frontier (`0.80` mean gates versus PPO best `1.66` mean
gates), but it is a valid MPPI preflight baseline because it now produces
repeatable, finite, measurable gate progress.

## Decision

Decision: `continue_same_hypothesis`

Continue MPPI-only tuning. Do not launch PPO training, BC, DAgger, teacher data
generation, or PPO fine-tuning.

The next MPPI work should focus on:

1. better gate-plane timing and vertical velocity braking;
2. explicit post-gate waypoint handoff to avoid same-step contact after gate
   pass;
3. obstacle clearance only after first-gate and second-gate stability improves;
4. scaling horizon/samples after the guide model reaches stable multi-gate
   progress on smoke seeds.

Do not run full `validation_unseen 101-200` hard eval yet. The current MPPI
controller is below the PPO frontier and should first beat the smoke/dev gate
progress baseline.
