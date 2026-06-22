# Level3 PPO Decision: Loop010 Gate Retention + Obstacle Safety

## Decision

Run one bounded reward-only trial from the current global best:

```text
lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt
```

Keep the accepted Stage 2 no-train-wrappers training config and hard-evaluate
on `level3_dr.toml`. This packet does not approve any observation, PPO,
network, algorithm, training-structure, or reward-channel change.

## Why This Branch

Loop 010 remains the only branch with non-zero hard-evaluator success:

```text
success_rate = 0.05
mean_time_s_success = 5.64
mean_gates = 0.80
crash_rate = 0.95
```

The signal is fragile. A 100-seed re-eval of the same checkpoint found only
`success_rate = 0.01`, and later checkpoints in the same run regressed to zero
success. Still, loop 010 is stronger hard-gate evidence than loop 011:

- loop 011 reduced gate pressure and raised commanded-tilt pressure; success
  dropped to `0.0` and crash returned to `1.0`.

## Subagent Consensus

- Evaluator reviewer: return to `loop010:15M`; keep gate pressure; only make a
  small active-safety adjustment.
- W&B reviewer: emphasize real gate/finish conversion, not speed-first and not
  heavy safety that suppresses gate passage.
- Reward tuning reviewer: keep loop 010 gate rewards, raise finish/obstacle
  safety gently, and avoid repeating the failed loop 011 direction.

## Reward Numbers

Use active reward numbers only:

```text
gate_stage_coef=14
gate_axis_coef=28
gate_bonus=220
gate_front_bonus=10
gate_back_bonus=45
finish_bonus=205
wrong_side_penalty=8
crash_penalty=65
obstacle_coef=6
obstacle_margin=0.22
timeout_penalty=80
time_penalty=0.01
act_coef=0.015
d_act_th_coef=0.075
d_act_xy_coef=0.08
cmd_tilt_coef=0.9
rpy_coef=0.75
tilt_limit_deg=38
tilt_excess_coef=14
```

Disabled reward channels must remain disabled:

```text
progress_coef=0
near_gate_coef=0
gate_plane_bonus=0
missed_gate_penalty=0
obstacle_clearance_coef=0
```

## Acceptance Gate

Prefer this branch only if the standard 20-seed hard evaluator improves over
loop 010 on primary metrics:

- `success_rate > 0.05`, or
- `crash_rate < 0.95` with `mean_gates >= 0.80` and W&B gate/finish conversion.

If any checkpoint has non-zero success, run a 100-seed official re-eval before
treating the result as robust progress.

Reject or hold if:

- `success_rate == 0.0`,
- `mean_gates < 0.80`,
- `timeout_rate > 0.10`, or
- W&B reward improves without evaluator gate/finish progress.

## Command Shape

Run one 30M chunk from loop 010 15M, checkpoint every 5M, and evaluate all six
checkpoints before post-run W&B-backed analysis. Do not use `--max-iterations`
above `1`.
