# V56 Task 1 Align Stabilization Analysis

## Summary

Task 1 tightened the `GeometricSlowGatePlanner` align-to-cross entry condition
and added explicit `gate_local_vx` trace support. The run stayed finite and did
not touch `config/level3.toml`, but it did not meet the v56 acceptance gate and
regressed versus the v55 500-step baseline.

## Fixed Evaluation

- Stage: `planner_integration_smoke`
- Seeds: `101-120`
- Steps: `500`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Metrics:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task1_align_stabilization_500step_metrics.json`
- Trace:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task1_align_stabilization_500step_trace.json`
- Compatibility checker:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task1_align_stabilization_500step_gate.json`

## Builder And Checker Gate

Changed files:

- `lsy_drone_racing/control/level3_reference_tracker.py`
- `lsy_drone_racing/control/level3_reference_tracker_controller.py`
- `scripts/check_level3_reference_tracker_smoke.py`
- `tests/unit/control/test_level3_reference_tracker_env.py`

The implementation:

- added `gate_local_axis_velocity_x`;
- changed cross entry to require `yz_error <= 0.22`;
- changed speed gating from world velocity norm to gate-local X speed
  `<= 0.85 m/s`;
- added `gate_local_vx` to controller diagnostics and trace rows;
- added tests for alignment-gated crossing and gate-local X velocity.

Local checks:

- `pixi run -e tests pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py`
  passed: `20 passed, 1 warning`.
- Read-only checker reported `ALL GREEN`: `config/level3.toml` unchanged,
  relevant pytest passed, ruff passed, and `git diff --check` was clean.

## V56 Target Result

V56 target:

- first-gate progress `20/20`
- gate0 pass `>=10/20`
- contact `<=8/20`
- early termination `<=6/20`
- all finite
- unchanged `config/level3.toml`

Task 1 result:

- first-gate progress: `19/20`
- gate0 pass: `2/20` seeds `113, 120`
- contact: `19/20`
- early termination: `2/20`
- all finite: `true`
- `config/level3.toml`: unchanged

Baseline comparison:

- baseline first-gate progress: `20/20`
- baseline gate0 pass: `3/20`
- baseline contact: `15/20`

The legacy `planner_integration_smoke` checker passed, but that checker only
requires `gate0_pass_count >= 1`. It is compatibility evidence only and is not
the v56 acceptance gate.

## Trace Findings

Trace now includes `gate_local_vx`. It does not yet include per-step
`aperture_y` and `aperture_z`, so exact `cross_entry_yz_error =
norm(gate_local_yz - aperture_yz)` cannot be reconstructed for every step from
the trace alone.

Read-only trace reviewer findings:

- phase-4 cross entries occurred in `9/20` seeds:
  `101, 102, 109, 111, 113, 115, 117, 119, 120`;
- only `2/9` cross-entry seeds passed gate0;
- raw gate-local Y/Z norm at cross entry had min/median/p75/max
  `0.138 / 0.237 / 0.283 / 0.315`;
- `abs(gate_local_vx)` at cross entry had min/median/p75/max
  `0.033 / 0.265 / 0.375 / 0.410`;
- desired speed in phase 4 remained `0.52 m/s`;
- near-plane cross-phase velocity often rose above `0.7 m/s`.

Failure buckets:

- passed gate0 then contacted later: `2` seeds `113, 120`
- contact before gate plane: `11` seeds
- contact near gate without pass: `4` seeds
- fake recover / crossed-plane timeout: `1` seed `106`
- immediate or early contact: `2` seeds `114, 118`

## Semantic Guard Failure

Read-only semantics reviewer reported `FAILED`.

`GeometricSlowGatePlanner` can still enter phase 5 recover without an
environment `target_gate` transition. The concrete trace evidence is seed `106`:

- `phase_id = 5`
- `pre_target_gate = post_target_gate = 0`
- `max_gate_index = 0`
- persisted for all `500` trace rows
- no real environment gate switch occurred

This violates the v56 semantic guard:

```text
Only environment target_gate transition counts as a real gate pass.
For the same target_gate, recover is forbidden.
```

## Main-Agent Diagnosis

Task 1 was a useful measurement pass, but not a promotion candidate. Tightening
align-to-cross alone did not convert first-gate progress into gate0 pass and
increased contact terminations. The larger issue is that the planner still has a
recover phase path that can activate from local X alone before the environment
has accepted the gate pass.

The next iteration should repair the recover semantics before trusting any
Task 2 cross-speed or Task 3 backout result.
