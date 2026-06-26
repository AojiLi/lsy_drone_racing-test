---
name: level3-geometric-planner-loop
description: Use when tuning, evaluating, or diagnosing the deterministic GeometricSlowGatePlanner gate-crossing strategy for Level3 on unchanged config/level3.toml, especially v56_geometric_gate_crossing_tuning_loop work involving align stabilization, cross speed, near-plane backout, recover-after-real-gate-switch logic, per-step trace metrics, or fixed seeds 101-120 planner smoke. Use this instead of level3-ppo-loop when the task says not to train PPO and only to adjust geometric planner/reference generation.
---

# Level3 Geometric Planner Loop

Use this workflow for `v56_geometric_gate_crossing_tuning_loop`.

The job is narrow:

```text
Level3 observation / gate geometry / visible obstacles
-> GeometricSlowGatePlanner reference trajectory
-> PPO tracker
-> roll / pitch / yaw / thrust
```

Tune only the deterministic geometric planner's gate-front reference strategy.
Do not train PPO, change PPO weights, change the tracker checkpoint, change
reward, modify observation layout, add MPPI, or edit `config/level3.toml`.

## Contract

- Immutable target config: `config/level3.toml`.
- Planner file: `lsy_drone_racing/control/level3_reference_tracker.py`.
- Controller diagnostics: `lsy_drone_racing/control/level3_reference_tracker_controller.py`.
- Evaluator: `scripts/evaluate_level3_tracker_stage.py`.
- Trace source: `scripts/check_level3_reference_tracker_smoke.py`.
- State file: `experiments/level3_ppo_loop/state.json`.
- Checkpoint for v56 smoke:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`.
- Fixed smoke seeds: `101-120`.
- Fixed smoke horizon: `500` Level3 env steps.
- Current baseline: `3/20` gate0 passes, `20/20` first-gate progress,
  `15/20` contact terminations.

## Objective

Improve first-gate crossing reliability before any long training:

```text
first-gate progress = 20/20
gate0 pass >= 10/20
contact <= 8/20
early termination <= 6/20
all_finite = true
config/level3.toml unchanged
```

If this gate passes, write a decision packet to promote to multi-gate planner
smoke. Do not call this a Level3 completion result.

## Required Loop Shape

Run one bounded planner-tuning iteration at a time:

```text
read latest trace analysis/state
-> choose exactly one v56 task hypothesis
-> builder changes only planner/evaluator diagnostics needed for that task
-> checker verifies tests, trace metrics, and unchanged config/level3.toml
-> run 500-step planner smoke on seeds 101-120
-> classify failures from trace
-> write analysis, decision, Chinese reader note, state update
-> commit and push
```

Use builder/checker for every code change. The builder may edit code; the
checker must be read-only and must report `ALL GREEN` or `FAILED` with concrete
evidence. The main agent owns the decision.

## V56 Tasks

### 1. Align Stabilization

Problem: many seeds reach the gate front with large Y/Z error but still enter
cross.

Allowed changes:

```text
enter cross only when aperture Y/Z error is below about 0.18m-0.22m
and gate-axis speed is modest
otherwise keep align or back out to pre-gate
```

Metrics:

```text
near_plane_yz_error_median <= 0.22
cross_entry_yz_error_p75 <= 0.25
wrong_cross_entry_count <= 3/20
```

### 2. Cross Slowdown

Problem: cross may be too fast for the tracker to finish centering.

Allowed changes:

```text
cross desired_speed in about 0.25-0.35 m/s
shorter and smoother cross reference
avoid large reference jumps around the plane
```

Metrics:

```text
gate0 pass >= 5/20
contact <= 12/20
cross_phase_contact_count decreases from baseline
```

### 3. Near-Plane Backout

Problem: if `abs(gate_local_x) < 0.35` but Y/Z is far from aperture, pushing
through the plane creates fake progress or contact.

Allowed changes:

```text
if abs(gate_local_x) < 0.35 and yz_error > 0.30:
    phase = align
    reference = pre_gate_align_point
```

Metrics:

```text
large_yz_cross_attempt_count <= 2/20
contact <= 10/20
gate0 pass does not fall below baseline 3/20
```

### 4. Recover After Real Gate Switch

Problem: local X alone can make the planner behave as if the gate was passed.

Allowed changes:

```text
enter recover / next-gate logic only after target_gate actually changes
or an explicit gate-pass trace condition is satisfied
```

Metrics:

```text
recover_before_gate_switch_count = 0
fake_recover_count = 0
gate0 pass >= 8/20
```

### 5. Formal 500-Step Smoke Gate

Run the fixed smoke:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage planner_integration_smoke \
  --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --seeds 101-120 \
  --level3-steps 500 \
  --early-termination-step-threshold 50 \
  --trace-output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_geometric_gate_crossing_500step_trace.json \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_geometric_gate_crossing_500step_metrics.json
```

Then run the gate checker if the existing gate spec is applicable:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage planner_integration_smoke \
  --metrics-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_geometric_gate_crossing_500step_metrics.json \
  --history-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_required_stage_history_through_zigzag.json \
  --require-prerequisites \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_geometric_gate_crossing_500step_gate.json
```

## Trace Analysis Requirements

Every v56 iteration must classify seeds into at least:

```text
passed_gate0_then_contact_later
contact_before_gate_plane
contact_near_gate_without_pass
crossed_plane_far_outside_aperture_timeout
immediate_or_early_contact
```

Also report:

```text
gate0 pass seeds
termination reason counts
near-plane Y/Z error for pass versus fail seeds
cross-entry Y/Z error distribution
recover-before-switch count
large-Y/Z cross attempt count
phase contact counts
```

If a required metric is not yet emitted, add the smallest evaluator/trace
support first, then rerun smoke. Do not infer success from hand-waving.

## Validation Commands

Before any smoke after code changes:

```bash
pixi run -e tests pytest tests/unit/scripts/test_level3_tracker_stage_evaluator.py tests/unit/control/test_level3_reference_tracker_env.py -q
pixi run -e tests ruff check scripts/check_level3_reference_tracker_smoke.py scripts/evaluate_level3_tracker_stage.py lsy_drone_racing/control/level3_reference_tracker.py lsy_drone_racing/control/level3_reference_tracker_controller.py
git diff -- config/level3.toml
```

After smoke, write:

- analysis packet under `experiments/level3_ppo_loop/analysis/`;
- decision packet under `experiments/level3_ppo_loop/decisions/`;
- plain Chinese note under `drone_notes/level3_loops/`;
- state update in `experiments/level3_ppo_loop/state.json`.

Commit and push intended small files. Do not commit checkpoints, W&B runs,
trace JSONs, metrics JSONs, caches, or logs unless the user explicitly asks.
