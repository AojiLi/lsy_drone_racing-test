# Level3 Loop 014 Reject / Hold Decision

## Decision

Reject `level3_loop_014_loop010_gate_retention_obstacle_safety`.

Do not continue from loop 014 checkpoints and do not continue the same
gate-retention plus obstacle-safety parameter direction automatically.

Keep the current global best:

```text
lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt
```

## Hard Evaluator Evidence

Loop 014 best checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_014_loop010_gate_retention_obstacle_safety/level3_loop_014_loop010_gate_retention_obstacle_safety_step_025000000.ckpt
```

Metrics:

```text
success_rate = 0.00
mean_time_s_success = None
mean_gates = 0.75
crash_rate = 1.00
timeout_rate = 0.00
target_met = False
```

All six evaluated loop 014 checkpoints had `0%` success and `100%` crash.
This is below the loop 010 incumbent:

```text
success_rate = 0.05
mean_time_s_success = 5.64
mean_gates = 0.80
crash_rate = 0.95
```

Loop 014 failed its own acceptance gate:

- no checkpoint reached non-zero success,
- no checkpoint reduced crash below `0.95`,
- best mean gates stayed below `0.80`,
- W&B reward movement did not convert into hard-evaluator progress.

## W&B Evidence

Loop 014 W&B run:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_014_loop010_gate_retention_obstacle_safety
```

Training reward increased, but task conversion did not:

```text
train/total_reward trend = up
race/passed_gate_rate tail_mean = 0.009837, flat
race/finished_rate tail_mean = 0.000081, flat
race/crashed_rate tail_mean = 0.010264, flat
```

PPO diagnostics did not indicate optimizer instability:

```text
losses/approx_kl tail_mean = 0.000775
losses/clipfrac tail_mean = 0.000305
```

The failure is behavioral reward-to-evaluator non-conversion, not a reason to
tune PPO hyperparameters inside this loop.

## Subagent Review

- Evaluator reviewer: reject loop 014 and keep loop 010 as global best.
- W&B reviewer: reject/hold; reward improved but passed-gate and finish curves
  stayed flat.
- Reward-only tuning reviewer: hold; do not launch another automatic
  reward-only chunk without a genuinely new active-reward hypothesis.

## Next Allowed Direction

Hold automatic training.

The next run, if any, must start from the current global best branch and must be
backed by a new decision packet. It must not repeat these already-failed lanes:

- loop 011 soft-gate / higher commanded-tilt pressure,
- loop 014 higher finish/obstacle/crash safety continuation,
- analyzer's generic low-pressure `13/24/200/175/time_penalty=0.02` suggestion
  unless a new packet explains why it is not just repeating earlier failures.

Keep disabled reward channels at zero and do not change observation, PPO,
network, algorithm, training structure, or reward channel set without a new
explicit escalation packet.
