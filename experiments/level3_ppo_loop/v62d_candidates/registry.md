# v62d Candidate Registry

This registry tracks the high-budget generic reference-tracker search. It is
not a final Level3 hard-eval leaderboard.

## Frontier Before v62d

Comparison baseline:

```text
v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

Under the 16-rollout tracker evaluation protocol:

| Metric | v62c 7M |
|---|---:|
| reward | -4.8459 |
| command position error | 0.6573 |
| cross-track error | 0.5214 |
| command velocity error | 0.7397 |
| done mean | 0.00391 |
| balanced score | -7.5365 |

## Candidates

| id | family | hypothesis | changed knobs | status | best checkpoint | decision |
|---|---|---|---|---|---|---|
| v62d_001 | A_value_return_stabilization | reduce critic target magnitude without changing rewards/obs | `value_target_scale=50.0`, `num_minibatches=8`, `update_epochs=4` | rejected_not_promoted | `v62d_001...step_005000000.pkl` | critic scale fixed, but velocity/done/action_delta regressed; next isolate conservative PPO |
| v62d_002 | D_PPO_stabilizer | test value scale under conservative v62c-like PPO update pressure | `value_target_scale=50.0`, `num_minibatches=4`, `update_epochs=1` | rejected_not_promoted | `v62d_002...step_005000000.pkl` | cleaner than v62d_001 but still worse than v62c 7M on velocity/done/action_delta; next switch to velocity reward numbers |
| v62d_003 | B_velocity_obedience_reward_numbers | strengthen generic command velocity obedience | `vel_error_coef=1.2`, `value_target_scale=1.0`, `num_minibatches=4`, `update_epochs=1` | rejected_not_promoted | `v62d_003...step_020000000.pkl` | 2.4% velocity gain is below promotion threshold and action delta worsened 7.9x; next switch to generator distribution |
| v62d_004 | C_generator_velocity_distribution | rebalance command generator speed bins and transitions | pending builder/checker | proposed_support | pending | implement speed-bin balanced generator support before 30M training |

## v62d_001 Result

Analysis:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_001_value_target_scale50_30m_analysis.md
```

Decision:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_001_decision.md
```

Best checkpoint inside this candidate:

```text
lsy_drone_racing/control/checkpoints/v62d_001_value_target_scale50_30m/v62d_001_value_target_scale50_30m_step_005000000.pkl
```

It is not promoted because velocity, done rate, reward, and action smoothness
all regressed versus the v62c 7M baseline.

| Metric | v62c 7M | v62d_001 best |
|---|---:|---:|
| reward | -4.8459 | -9.7541 |
| command position error | 0.6573 | 0.2851 |
| cross-track error | 0.5214 | 0.2633 |
| command velocity error | 0.7397 | 1.2018 |
| done mean | 0.00391 | 0.02903 |
| action delta | 0.000006 | 0.01675 |
| balanced score | -7.5365 | -11.9443 |

Next recommended candidate:

```text
v62d_002_value_scale50_conservative_ppo
```

Keep `value_target_scale=50.0`, but restore conservative v62c-like PPO update
pressure:

```text
--num-minibatches 4
--update-epochs 1
```

## v62d_002 Plan

Hypothesis:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_002_hypothesis.md
```

This candidate isolates the PPO-update-pressure confounder from `v62d_001`.
It trains from scratch for 30,015,488 steps with the same value target scale but
with `4` minibatches and `1` update epoch.

## v62d_002 Result

Analysis:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_002_value_scale50_conservative_ppo_30m_analysis.md
```

Decision:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_002_decision.md
```

Best checkpoint inside this candidate:

```text
lsy_drone_racing/control/checkpoints/v62d_002_value_scale50_conservative_ppo_30m/v62d_002_value_scale50_conservative_ppo_30m_step_005000000.pkl
```

It is not promoted. It is much cleaner than v62d_001, but it still fails the
v62c 7M frontier on velocity, done rate, reward, action smoothness, and
balanced score.

| Metric | v62c 7M | v62d_002 best |
|---|---:|---:|
| reward | -4.8459 | -6.9258 |
| command position error | 0.6573 | 0.4066 |
| cross-track error | 0.5214 | 0.3439 |
| command velocity error | 0.7397 | 0.7721 |
| done mean | 0.00391 | 0.01615 |
| action delta | 0.000006 | 0.00276 |
| balanced score | -7.5365 | -9.0010 |

Next recommended candidate:

```text
v62d_003_velocity_coef_2x
```

Switch to Family B velocity-obedience reward numbers, with one generic tracker
reward knob:

```text
ReferenceCommandReward vel_error_coef: 0.6 -> 1.2
```

Return to v62c-style update/value settings:

```text
value_target_scale=1.0
num_minibatches=4
update_epochs=1
```

## v62d_003 Support

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_003_velocity_coef_2x_support.md
```

Hypothesis:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_003_hypothesis.md
```

The support change adds an explicit training CLI knob:

```text
--command-vel-error-coef 1.2
```

Checker result:

```text
ALL GREEN
```

The checker verified default behavior is unchanged when the flag is omitted,
the override only affects clean command reward `vel_error_coef`, checkpoint and
summary metadata record the coefficient, and both `config/level3.toml` and
`config/level3_tracker_free_space.toml` remain unchanged.

## v62d_003 Result

Analysis:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_003_velocity_coef_2x_30m_analysis.md
```

Decision:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_003_decision.md
```

Best checkpoint inside this candidate:

```text
lsy_drone_racing/control/checkpoints/v62d_003_velocity_coef_2x_30m/v62d_003_velocity_coef_2x_30m_step_020000000.pkl
```

It is not promoted. It is the best v62d_003 milestone, but it only improves
velocity by `2.4%`, below the `10%-15%` promotion threshold, and action delta
worsens by `7.9x` versus v62c 7M.

| Metric | v62c 7M | v62d_003 best |
|---|---:|---:|
| reward | -4.8459 | -5.1643 |
| command position error | 0.6573 | 0.6381 |
| cross-track error | 0.5214 | 0.5022 |
| command velocity error | 0.7397 | 0.7219 |
| done mean | 0.00391 | 0.00391 |
| action delta | 0.000006 | 0.000050 |
| balanced score | -7.5365 | -7.7744 |

Post-audit on the best checkpoint passed:

```text
action_clipping=ok
action_sampling_logprob=ok
advantage_scale=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=3.10e-7
```

The failure is behavioral rather than action-distribution math. A blunt
velocity reward coefficient increase did not teach sufficient speed obedience.

Next recommended candidate:

```text
v62d_004_speed_bin_balanced_generator
```

Switch to Family C generator velocity distribution:

```text
rebalance command generator toward explicit speed bins,
longer constant-speed windows,
brake ramps,
low-speed-through windows,
and recover-speed transitions.
```

Keep v62c-style PPO/reward settings unless the v62d_004 support packet
explicitly changes them:

```text
command_vel_error_coef=default
value_target_scale=1.0
num_minibatches=4
update_epochs=1
```

## v62d_004 Plan

Hypothesis:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_004_hypothesis.md
```

This candidate changes generator semantics, so builder/checker support is
required before any 30M training. It must keep `config/level3.toml` unchanged,
keep actor observation `level3_reference_tracker_command_v3`, and avoid all
gate/aperture/race/finish/stage rewards.
