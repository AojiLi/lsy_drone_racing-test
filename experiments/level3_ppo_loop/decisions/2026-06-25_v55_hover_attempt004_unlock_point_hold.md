# v55 Tracker Decision: Hover Passed, Unlock Point Hold

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
hover
```

Next stage:

```text
point_hold
```

## Decision

Attempt004 passed the hover gate. The tracker ladder should now advance to
`point_hold`.

Use this checkpoint as the preferred initialization for the next stage:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/v55_tracker_hover_pd_warmstart_attempt004_final.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_hover_pd_warmstart_attempt004_final_metrics.json
```

Key metrics:

```text
success_rate = 1.0
crash_rate = 0.0
mean_position_error_m = 0.05920039489865303
p90_position_error_m = 0.08545919507741928
mean_speed_mps = 0.03472756966948509
mean_action_delta_l2 = 0.004586467053741217
```

## Next Action

Train `point_hold` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 2000000
--checkpoint-interval 500000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/v55_tracker_hover_pd_warmstart_attempt004_final.ckpt
```

Evaluate all `point_hold` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage point_hold` before
unlocking `point_reach`.

Do not launch planner-driven Level3 training yet. Only `hover` has passed.
