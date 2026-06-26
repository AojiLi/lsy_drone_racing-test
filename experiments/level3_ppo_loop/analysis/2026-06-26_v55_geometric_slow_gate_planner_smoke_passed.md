# v55 Analysis: GeometricSlowGatePlanner Planner Smoke Passed

## Summary

Formal `planner_integration_smoke` passed on unchanged `config/level3.toml`.

Command:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage planner_integration_smoke \
  --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --seeds 101-120 \
  --level3-steps 150 \
  --early-termination-step-threshold 50 \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_geometric_slow_gate_planner_smoke_101_120_metrics.json
```

Gate checker:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage planner_integration_smoke \
  --metrics-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_geometric_slow_gate_planner_smoke_101_120_metrics.json \
  --history-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_required_stage_history_through_zigzag.json \
  --require-prerequisites \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_geometric_slow_gate_planner_smoke_101_120_gate.json
```

Result:

```text
passed = true
next_stage_unlocked = manual_long_level3_training_review
```

## Metrics

```text
checkpoint_backed = true
all_finite = true
level3_toml_diff_clean = true
episodes = 20
seeds = 101-120
nonzero_first_gate_progress_count = 20
nonzero_first_gate_progress_ratio = 1.0
gate0_pass_count = 1
gate0_pass_seeds = [113]
early_termination_count = 2
early_termination_ratio = 0.1
first_gate_axis_gain_mean = 0.8791520540602505
first_gate_axis_gain_min = 0.07826706767082214
first_gate_axis_gain_max = 1.771201230585575
```

Gate checker thresholds:

```text
nonzero_first_gate_progress_ratio >= 0.5  passed: 1.0
gate0_pass_count >= 1                    passed: 1
early_termination_ratio <= 0.6            passed: 0.1
```

## Interpretation

This is a real improvement over the prior micro-smoke state. The closed loop:

```text
GeometricSlowGatePlanner -> PPO reference tracker -> roll/pitch/yaw/thrust
```

now produces measurable first-gate progress on every validation seed and one
actual gate0 pass on seed `113`.

This does not mean Level3 is solved. It only proves the planner-tracker
interface is alive enough to pass the strict planner smoke gate. Most seeds did
not pass gate0 within 150 steps, and several episodes terminated before the
step limit. The next stage should inspect whether failures come from:

- planner references that are too close, too aggressive, or badly phased;
- tracker inability to follow the planner's gate-frame reference family;
- gate switch / target gate hysteresis after first gate;
- obstacle-offset geometry around the first gate.

## Next Action

Unlock `manual_long_level3_training_review`. Do not launch a long Level3
planner-tracker experiment automatically from this smoke result. The next
decision should decide whether to:

- run a longer planner smoke horizon;
- add planner-reference diagnostics/trajectory dumps;
- tune the geometric planner's speeds and phase thresholds;
- train a tracker stage directly on planner-generated trajectories;
- or approve a bounded longer Level3 planner-tracker run.
