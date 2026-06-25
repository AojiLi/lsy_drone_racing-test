# v55 Tracker Decision: Curve Tracking Passed, Unlock Zigzag/Lemniscate Tracking

Date: 2026-06-26

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
curve_tracking
```

Next stage:

```text
zigzag_or_lemniscate_tracking
```

## Decision

`curve_tracking` passed its qualification gate. Advance the tracker ladder to
`zigzag_or_lemniscate_tracking`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/curve_tracking/v55_tracker_curve_from_l_shape_attempt001_step_034958400.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_curve_from_l_shape_attempt001_step9m_metrics.json
```

Key metrics:

```text
path_completion_rate = 1.0
crash_rate = 0.0
mean_cross_track_error_m = 0.09281318634748459
p90_cross_track_error_m = 0.2037346214056015
oscillation_score = 0.010572141967713833
mean_action_delta_l2 = 0.009870258159935474
```

## Next Action

Train `zigzag_or_lemniscate_tracking` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 12000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/curve_tracking/v55_tracker_curve_from_l_shape_attempt001_step_034958400.ckpt
```

Evaluate all `zigzag_or_lemniscate_tracking` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage zigzag_or_lemniscate_tracking`
with prerequisite history before unlocking `gate_aperture_reference`.

Do not launch planner-driven Level3 training yet. The tracker still needs sharp
curve, gate-aperture, and planner integration gates.
