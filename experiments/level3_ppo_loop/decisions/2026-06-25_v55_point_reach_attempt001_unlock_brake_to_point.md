# v55 Tracker Decision: Point Reach Passed, Unlock Brake To Point

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
point_reach
```

Next stage:

```text
brake_to_point
```

## Decision

`point_reach` passed its qualification gate. The tracker ladder should advance
to `brake_to_point`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/point_reach/v55_tracker_point_reach_from_point_hold_attempt001_final.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_point_reach_from_point_hold_attempt001_final_metrics.json
```

Key metrics:

```text
success_rate = 1.0
crash_rate = 0.0
mean_final_position_error_m = 0.02291424199938774
p90_final_position_error_m = 0.023098517209291458
mean_overshoot_m = 0.0005792942829430103
mean_time_to_target_s = 1.5090000629425049
```

## Next Action

Train `brake_to_point` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 4000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/point_reach/v55_tracker_point_reach_from_point_hold_attempt001_final.ckpt
```

Evaluate all `brake_to_point` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage brake_to_point` with
prerequisite history before unlocking `line_tracking`.

Do not launch planner-driven Level3 training yet. Only `hover`, `point_hold`,
and `point_reach` have passed.
