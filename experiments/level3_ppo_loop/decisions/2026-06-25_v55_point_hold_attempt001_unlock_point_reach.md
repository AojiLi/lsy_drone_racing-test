# v55 Tracker Decision: Point Hold Passed, Unlock Point Reach

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
point_hold
```

Next stage:

```text
point_reach
```

## Decision

`point_hold` passed its qualification gate. The tracker ladder should advance
to `point_reach`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/point_hold/v55_tracker_point_hold_from_hover_attempt001_final.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_point_hold_from_hover_attempt001_final_metrics.json
```

Key metrics:

```text
success_rate = 1.0
crash_rate = 0.0
mean_final_position_error_m = 0.018528476357460022
p90_final_position_error_m = 0.019227204844355583
mean_terminal_speed_mps = 0.00030724474345333874
mean_overshoot_m = 0.0
hold_time_ratio = 0.8660999536514282
```

## Next Action

Train `point_reach` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 4000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/point_hold/v55_tracker_point_hold_from_hover_attempt001_final.ckpt
```

Evaluate all `point_reach` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage point_reach` with
prerequisite history before unlocking `brake_to_point`.

Do not launch planner-driven Level3 training yet. Only `hover` and
`point_hold` have passed.
