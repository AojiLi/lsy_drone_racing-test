# v55 Tracker Decision: L-Shape Tracking Passed, Unlock Curve Tracking

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
l_shape_tracking
```

Next stage:

```text
curve_tracking
```

## Decision

`l_shape_tracking` passed its qualification gate. Advance the tracker ladder to
`curve_tracking`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/l_shape_tracking/v55_tracker_l_shape_from_multi_point_attempt001_step_025958208.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_l_shape_from_multi_point_attempt001_step5m_metrics.json
```

Key metrics:

```text
corner_completion_rate = 1.0
crash_rate = 0.0
mean_cross_track_error_m = 0.118613600730896
p90_cross_track_error_m = 0.20258449018001556
mean_corner_overshoot_m = 0.09654346853494644
mean_action_delta_l2 = 0.010565461590886116
```

## Next Action

Train `curve_tracking` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 10000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/l_shape_tracking/v55_tracker_l_shape_from_multi_point_attempt001_step_025958208.ckpt
```

Evaluate all `curve_tracking` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage curve_tracking` with
prerequisite history before unlocking `zigzag_or_lemniscate_tracking`.

Do not launch planner-driven Level3 training yet. The tracker still needs
curve, sharp curve, gate-aperture, and planner integration gates.
