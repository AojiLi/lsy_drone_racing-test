# Level3 PPO Stage 2 Decision: Accept No-Train-Wrappers, Continue With Soft Gate Safety

## Decision

Accept `stage2_no_train_wrappers` as the current Stage 2 branch, but treat it as
a fragile breakthrough rather than stable Level3 competence.

The next train/eval chunk should continue from the 010 15M checkpoint, keep the
same no-train-wrappers training config, and make one small reward-number move
toward softer gate chasing plus slightly stronger commanded-tilt pressure.

## Evidence

Standard hard eval on `level3_dr.toml` selected:

```text
level3_loop_010_stage2_no_train_wrappers:15M
success_rate = 0.05
crash_rate = 0.95
mean_gates = 0.8
mean_time_s_success = 5.64
```

The branch meets the Stage 2 acceptance gate because hard eval produced
non-zero success and crash rate below 1.0.

The signal is weak:

- A 100-seed official re-eval of the same checkpoint found `success_rate = 0.01`
  and `crash_rate = 0.99`.
- The one success was seed `3`, also the success seen in the original 20-seed
  evaluator.
- W&B does not show strong conversion: `race/passed_gate_rate` and
  `race/finished_rate` remain nearly flat, while later 20M/25M/final
  checkpoints returned to `0%` success.
- Crash taxonomy remains concentrated around early gates and obstacles.

## Subagent Consensus

- Evaluator reviewer: accept 010 15M as the new global best, but do not treat it
  as close to target.
- W&B reviewer: weak positive signal, no PPO instability, no clear conversion.
- Tuning reviewer: continue the no-train-wrappers branch with a small
  soft-gate/safety move; do not change algorithm, observation, network, or PPO
  hyperparameters.

## Next Reward Numbers

Start from 010 15M and change only:

```text
gate_axis_coef: 28 -> 26
gate_bonus: 220 -> 210
gate_back_bonus: 45 -> 40
cmd_tilt_coef: 0.9 -> 1.0
```

Keep the rest of the active reward numbers at the 010 values:

```text
gate_stage_coef=14
gate_front_bonus=10
finish_bonus=190
wrong_side_penalty=8
crash_penalty=55
obstacle_coef=5.25
obstacle_margin=0.2
timeout_penalty=80
time_penalty=0.015
act_coef=0.015
d_act_th_coef=0.075
d_act_xy_coef=0.08
rpy_coef=0.75
tilt_limit_deg=38
tilt_excess_coef=14
```

Disabled reward channels remain zero.

## Acceptance Gate For Next Chunk

Prefer the next branch only if standard hard eval on `level3_dr.toml` improves
over 010 15M on at least one primary metric:

- `success_rate > 0.05`
- `crash_rate < 0.95`
- clear W&B gate/finish conversion that is confirmed by evaluator metrics

If standard hard eval shows non-zero success, run a 100-seed official re-eval of
the best checkpoint before treating it as robust progress.

Reject or hold if the branch returns to `0%` success and `100%` crash without
W&B conversion.
