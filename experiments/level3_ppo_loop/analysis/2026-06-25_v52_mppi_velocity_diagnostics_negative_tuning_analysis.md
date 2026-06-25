# V52 MPPI Velocity Diagnostics And Negative Tuning Analysis

Date: 2026-06-25

Lane: `v52_mppi_oracle_teacher_level3`

Controller: `lsy_drone_racing/control/mppi_level3_oracle.py`

Evaluator: `scripts/evaluate_level3_controller.py`

Target config: unchanged `config/level3.toml`

## Summary

This loop stayed MPPI-only. It did not launch PPO, BC, DAgger, imitation
learning, teacher dataset generation, or PPO fine-tuning.

No MPPI controller change from this tuning round was retained, because none
improved the current v52 smoke/dev baseline. The retained source change is an
evaluator diagnostic improvement: episode rows and summaries now include
terminal speed and terminal velocity in the active target-gate frame.

Retained smoke result on seeds `101-105` with the new diagnostics:

- success: `0/5` = `0%`;
- mean gates: `0.80`;
- crash: `100%`;
- finite action rate: `100%`;
- mean endpoint speed: `1.740 m/s`;
- mean absolute gate-frame terminal velocity:
  - `vx`: `1.274 m/s`;
  - `vy`: `0.563 m/s`;
  - `vz`: `0.750 m/s`;
- endpoint classes: `{"gate_side_frame": 2, "near_gate_obstacle": 3}`.

Retained dev result on seeds `1-10` with the new diagnostics:

- success: `0/10` = `0%`;
- mean gates: `0.20`;
- crash: `100%`;
- finite action rate: `100%`;
- mean endpoint speed: `1.612 m/s`;
- mean absolute gate-frame terminal velocity:
  - `vx`: `1.128 m/s`;
  - `vy`: `0.710 m/s`;
  - `vz`: `0.730 m/s`;
- endpoint classes: `{"gate_side_frame": 8, "gate_vertical_frame": 2}`.

The current PPO frontier remains unchanged and is not overwritten by MPPI:

- success: `21%`;
- mean gates: `1.66`;
- crash: `79%`;
- mean successful time: `7.578s`;
- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt`.

## Tuning Attempts Rejected

The following MPPI controller changes were tested and reverted:

- `v23` frame contact cost plus bad crossing-speed cost:
  smoke dropped to `0.40` mean gates;
- `v24` softer frame/crossing cost:
  smoke dropped to `0.20` mean gates;
- `v25` horizon `60` and samples `768`:
  smoke dropped to `0.40` mean gates;
- `v26` horizon `42` and samples `768`:
  smoke dropped to `0.20` mean gates;
- `v27` corridor obstacle staging with `0.18m` lateral pre-gate offset:
  smoke dropped to `0.60` mean gates;
- `v28` softer corridor staging with `0.10m` offset:
  smoke stayed at `0.60` mean gates and dev stayed at `0.20`;
- `v29` small positive gate-height bias:
  smoke tied `0.80` but dev dropped to `0.10`;
- `v30` guide-heavy first-action blend:
  smoke dropped to `0.40`;
- `v31` MPPI-heavy first-action blend:
  smoke dropped to `0.40`;
- `v32` avoiding/scoring only currently observed obstacles:
  smoke dropped to `0.60`;
- `v34` gate-axis speed limiting near the gate plane:
  smoke tied `0.80` and dev stayed at `0.20`, with solved seeds changing
  rather than improving.

Because these changes failed to improve success, mean gates, or crash rate,
they are not retained.

## Failure Analysis

The new endpoint velocity diagnostics show that the current MPPI controller is
not merely clipping the gate by a static position error. Many terminal contacts
also have significant residual gate-frame velocity:

- smoke mean `|target_local_vx|` is `1.274 m/s`;
- smoke mean `|target_local_vy|` is `0.563 m/s`;
- smoke mean `|target_local_vz|` is `0.750 m/s`;
- dev mean `|target_local_vy|` and `|target_local_vz|` are both around
  `0.7 m/s`.

This means the next useful controller change should not be another scalar
penalty bolted onto the current short-horizon point-mass MPPI. It should change
the local gate controller so it explicitly regulates velocity in gate
coordinates:

- approach speed along gate x;
- lateral velocity along gate y;
- vertical velocity along gate z;
- handoff timing after a gate is passed.

The negative tests also show that increasing MPPI compute budget alone makes
the controller more confident in a flawed cost/model rather than more capable.

## Decision

Decision: `continue_same_hypothesis`

Continue MPPI-only tuning, but do not run full `validation_unseen 101-200` yet
and do not generate PPO teacher data. Current MPPI remains below the PPO
frontier.

Next MPPI work should use the new velocity diagnostics to implement a more
structured gate-frame velocity controller or a better rollout/contact model,
then re-test on smoke and dev before any full hard eval.
