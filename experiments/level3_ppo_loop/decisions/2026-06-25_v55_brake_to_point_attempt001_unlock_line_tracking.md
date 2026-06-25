# v55 Tracker Decision: Brake To Point Passed, Unlock Line Tracking

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
brake_to_point
```

Next stage:

```text
line_tracking
```

## Decision

`brake_to_point` passed its qualification gate. The tracker ladder should
advance to `line_tracking`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/brake_to_point/v55_tracker_brake_to_point_from_point_reach_attempt001_final.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_brake_to_point_from_point_reach_attempt001_final_metrics.json
```

Key metrics:

```text
brake_success_rate = 1.0
crash_rate = 0.0
mean_terminal_speed_mps = 0.0007754218531772494
p90_terminal_speed_mps = 0.0011556519893929362
mean_overshoot_m = 0.0
p90_overshoot_m = 0.0
```

## Next Action

Train `line_tracking` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 5000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/brake_to_point/v55_tracker_brake_to_point_from_point_reach_attempt001_final.ckpt
```

Evaluate all `line_tracking` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage line_tracking` with
prerequisite history before unlocking `heading_tracking`.

Do not launch planner-driven Level3 training yet. The tracker has passed point
servo and braking tasks, but not line, heading, multi-point, curves, gate
aperture, or planner integration.
