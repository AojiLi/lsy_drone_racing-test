# v55 Tracker Decision: Line Tracking Passed, Unlock Heading Tracking

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
line_tracking
```

Next stage:

```text
heading_tracking
```

## Decision

`line_tracking` passed its qualification gate. The tracker ladder should
advance to `heading_tracking`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/line_tracking/v55_tracker_line_tracking_terminal_hold_position_attempt002_final.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_line_tracking_terminal_hold_position_attempt002_final_metrics.json
```

Key metrics:

```text
success_rate = 1.0
crash_rate = 0.0
mean_cross_track_error_m = 0.07652631402015686
p90_cross_track_error_m = 0.19432517886161804
mean_speed_error_mps = 0.0721852257847786
mean_action_delta_l2 = 0.012063540518283844
```

## Next Action

Train `heading_tracking` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 4000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/line_tracking/v55_tracker_line_tracking_terminal_hold_position_attempt002_final.ckpt
```

Evaluate all `heading_tracking` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage heading_tracking` with
prerequisite history before unlocking `multi_point_reference`.

Do not launch planner-driven Level3 training yet. The tracker still needs
heading, multi-point, L-shape, curve, sharp curve, gate-aperture, and planner
integration gates.
