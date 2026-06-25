# V52 MPPI Post-Gate Prealign And Taxonomy Analysis

Date: 2026-06-25

Lane: `v52_mppi_oracle_teacher_level3`

Controller: `lsy_drone_racing/control/mppi_level3_oracle.py`

Evaluator: `scripts/evaluate_level3_controller.py`

Target config: unchanged `config/level3.toml`

## Summary

This loop kept the work MPPI-only. It did not launch PPO, BC, DAgger,
imitation learning, teacher data generation, or PPO fine-tuning.

Retained changes:

- add a conservative post-first-gate prealignment branch in the MPPI guide;
- fix the non-PPO evaluator crash taxonomy to classify the terminal pre-step
  position instead of the disabled-drone warped position.

Latest retained smoke result on seeds `101-105`:

- success: `0/5` = `0%`;
- mean gates: `0.80`;
- crash: `5/5` = `100%`;
- timeout: `0/5` = `0%`;
- finite action rate: `100%`;
- termination reasons: `{"contact": 5}`;
- endpoint classes after taxonomy fix:
  `{"gate_side_frame": 2, "near_gate_obstacle": 3}`;
- best single-seed progress: seed `103` reached gate index `2`.

Latest retained dev result on seeds `1-10`:

- success: `0/10` = `0%`;
- mean gates: `0.20`;
- crash: `10/10` = `100%`;
- finite action rate: `100%`;
- endpoint classes after taxonomy fix:
  `{"gate_side_frame": 8, "gate_vertical_frame": 2}`.

The current PPO frontier remains unchanged and is not overwritten by MPPI:

- success: `21%`;
- mean gates: `1.66`;
- crash: `79%`;
- mean successful time: `7.578s`;
- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt`.

## What Was Tried

Retained:

- `v13/v16/v19/v22` post-gate prealign: for target gates after gate 0, if the
  drone is still far before the next gate and lateral/vertical error is high,
  aim slightly before the gate and reduce horizontal speed. This did not raise
  aggregate smoke mean gates above `0.80`, but it preserved the best observed
  multi-gate progress and made seed `103` survive to `4.98s` at gate 2.

Rejected during this loop:

- aperture/lateral offset around obstacles: reduced smoke mean gates to
  `0.40` or `0.20`;
- stronger obstacle clearance: reduced smoke mean gates to `0.20`;
- first-gate prealign: reduced smoke mean gates to `0.60`;
- takeoff-stabilize branch: reduced smoke mean gates to `0.20`;
- near-plane forced alignment plus smoother action filtering: did not improve
  smoke and shortened the best multi-gate seed;
- obstacle-detour waypoint: reduced smoke mean gates to `0.20`;
- gate-aperture obstacle offset: tied smoke at `0.80` but regressed dev mean
  gates to `0.10`.

## Failure Analysis

The evaluator taxonomy fix changed the interpretation materially. Previous
MPPI endpoint labels often looked like `bounds_or_ground`, because disabled
drones are warped below the track after contact. Using the pre-terminal
position shows that the retained controller is failing mostly through:

- first-gate and later-gate side-frame contact;
- near-gate obstacle contact;
- vertical-frame contact on the dev seeds.

This means the current MPPI controller is not yet limited by sample count or
full validation coverage. It is still limited by the quality of the local guide
and simplified rollout objective:

- it approaches gates but often reaches the plane with too much lateral or
  height error;
- obstacle avoidance that is independent from gate aperture hurts gate
  acquisition;
- gate-aperture offsets can trade obstacle collisions for frame collisions;
- the simplified point-mass rollout is not yet predicting the real contact
  geometry well enough to produce stable multi-gate flight.

## Decision

Decision: `continue_same_hypothesis`

Continue MPPI-only tuning. Do not run full `validation_unseen 101-200` yet,
because the retained controller is still below the PPO frontier and has `0%`
success on both smoke and dev.

Next MPPI work should focus on a stronger controller architecture rather than
small scalar cost tweaks:

1. use the corrected crash taxonomy and trace tooling before each larger
   controller change;
2. add a gate-frame velocity policy that explicitly limits crossing speed when
   lateral/vertical aperture error is high;
3. make obstacle avoidance gate-aware, so it selects a feasible pass side
   through the gate aperture instead of creating a large detour;
4. improve the rollout model/contact cost to penalize gate side/top/bottom
   frame intersections before the real simulator contact;
5. only scale MPPI horizon/samples after smoke/dev show stable multi-gate
   progress.

Teacher-data generation remains closed.
