# v55 Tracker Decision: Heading Tracking Passed, Unlock Multi-Point Reference

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
heading_tracking
```

Next stage:

```text
multi_point_reference
```

## Decision

`heading_tracking` passed its qualification gate. Advance the tracker ladder to
`multi_point_reference`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/heading_tracking/v55_tracker_heading_tracking_from_line_attempt001_step_019956864.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_heading_tracking_from_line_attempt001_step2m_metrics.json
```

Key metrics:

```text
success_rate = 1.0
crash_rate = 0.0
mean_heading_error_rad = 0.1475260853767395
p90_heading_error_rad = 0.1533883810043335
mean_yaw_rate_abs = 0.0
mean_action_delta_l2 = 0.007741902954876423
```

## Next Action

Train `multi_point_reference` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 8000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/heading_tracking/v55_tracker_heading_tracking_from_line_attempt001_step_019956864.ckpt
```

Evaluate all `multi_point_reference` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage multi_point_reference`
with prerequisite history before unlocking `l_shape_tracking`.

Do not launch planner-driven Level3 training yet. The tracker still needs
multi-point, L-shape, curve, sharp curve, gate-aperture, and planner integration
gates.
