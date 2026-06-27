# v62d_006 Subagent Reviews

Date: 2026-06-27

## tracker_eval_metrics

Verdict: do not promote `v62d_006`. Best milestone is `20M`:

```text
lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_30m/v62d_006_speedbin_longrollout_256x128_30m_step_020000000.pkl
```

Primary evidence:

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5M | -2.1458 | 0.2101 | 0.1793 | 0.8196 | 0.00000 | 0.000020 | -3.4497 |
| 10M | -2.1242 | 0.2063 | 0.1750 | 0.8079 | 0.00000 | 0.000051 | -3.4053 |
| 15M | -2.1781 | 0.2140 | 0.1837 | 0.8359 | 0.00000 | 0.000027 | -3.5086 |
| 20M | -2.0644 | 0.1964 | 0.1640 | 0.7789 | 0.00000 | 0.000092 | -3.2878 |
| 25M | -2.1697 | 0.2135 | 0.1830 | 0.8319 | 0.00000 | 0.000059 | -3.4952 |
| 30M/final | -2.5122 | 0.2608 | 0.2345 | 1.0318 | 0.00000 | 0.000174 | -4.1597 |

Comparison of v62d_006 20M:

| comparator | result |
|---|---|
| v62c 7M default | much better position/cross-track, but velocity is `5.3%` worse and action delta is `14.4x` higher |
| v62c 7M speed-bin | position `6.2%` better, cross-track `8.2%` better, velocity only `4.8%` better, action delta `2.7x` worse |
| v62d_004 5M | slightly worse reward, position, cross-track, velocity, and balanced score; action delta is better |
| v62d_005 15M | clearly better across reward, position, cross-track, velocity, done, and action smoothness |

Failure modes:

```text
best checkpoint is 20M, not final
30M/final degrades sharply
velocity gain is below the promotion threshold
no formal per-command stage metrics for brake/hold or slow-through were produced
```

## tracker_wandb_ppo

Verdict: do not promote `v62d_006` final or continue it to 60M. The useful
checkpoint is `20M`, but it is a near-tie with `v62d_004 5M`, not a clean new
frontier.

PPO health:

```text
steady-state throughput: ~416.8k env steps/s
steady-state PyTorch ratio: ~10.47x
action clipping: 0.0
stored-vs-env logprob error: ~3.2e-7
best-checkpoint action_sampling_logprob: ok
best-checkpoint advantage_scale: ok
```

The longer rollout is valid but slower than `1024x32`. The best audit passes
the action/logprob/advantage checks, but value prediction remains suspiciously
flat:

```text
best-audit value std: 0.0015
best-audit return std: 3.4640
```

Late PPO pressure is also visible:

```text
final approx_kl: 0.0468
final clip_fraction: 0.3330
final explained_variance: 0.1739
```

Behavior peaks at `20M`:

```text
reward: -2.0644
position error: 0.1964
cross-track: 0.1640
velocity error: 0.7789
done: 0.0
```

Final drifts:

```text
reward: -2.5122
position error: 0.2608
cross-track: 0.2345
velocity error: 1.0318
action_delta: 0.000174
```

Recommendation: keep tanh/logprob and speed-bin evidence. Do not carry forward
`256x128` as the next base. The next PPO stabilizer should eventually address
update pressure and critic/return scale, but reward tuning should still remain
within generic command-tracker terms.

## tracker_structure_research

Verdict: do not promote `v62d_006`.

The long-rollout knob is not broken, but it does not solve velocity obedience.
It is slightly smoother than `v62d_004`, but velocity is still worse than v62c
7M and slightly worse than v62d_004. Final/30M drifts down, so `256x128` should
not become the next base.

Recommended next candidate:

```text
v62d_007_speedbin_velocity_coef_2x_30m
Family E: best-of-family combination
```

Knobs:

```text
command_generator_profile=speed_bin_balanced
command_vel_error_coef=1.2
num_envs=1024
num_steps=32
value_target_scale=1.0
num_minibatches=4
update_epochs=1
action_distribution=tanh_squashed_gaussian
train from scratch
```

Rationale:

```text
v62d_004 gave the best useful generator/spatial signal.
v62d_003 gave the only direct velocity improvement signal, though too weak alone.
v62d_006 showed longer temporal credit does not solve velocity obedience.
```

Guardrails:

```text
clean command-v3 observation
tanh action
no gate/aperture/race/finish/stage rewards
no gate/obstacle/planner-phase actor inputs
unchanged config/level3.toml
```
