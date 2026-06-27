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
| v62d_004 | C_generator_velocity_distribution | rebalance command generator speed bins and transitions | `command_generator_profile=speed_bin_balanced`, defaults preserved | rejected_not_promoted | `v62d_004...step_005000000.pkl` | useful distribution signal, but velocity gain below threshold and action_delta worsened |
| v62d_005 | A_value_return_stabilization | stabilize critic/value scale under speed-bin generator | `command_generator_profile=speed_bin_balanced`, `value_target_scale=10.0` | rejected_not_promoted | `v62d_005...step_015000000.pkl` | critic diagnostics improved, but velocity/action smoothness regressed badly |
| v62d_006 | D_PPO_stabilizer | give brake/slow/recover behavior longer temporal credit | `command_generator_profile=speed_bin_balanced`, `num_envs=256`, `num_steps=128` | support_passed_ready_to_train | pending | support ALL GREEN; launch one 30M from scratch |

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

## v62d_004 Support

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_004_speed_bin_balanced_generator_support.md
```

Decision packet:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_004_support_decision.md
```

The support change adds a gated command-generator profile:

```text
--command-generator-profile speed_bin_balanced
```

Checker result:

```text
ALL GREEN
```

The checker verified default generator behavior is preserved unless the new
profile is selected, the formal trainer and audit paths propagate the profile,
checkpoint/summary metadata record it, smoke/audit checks pass, and both
`config/level3.toml` and `config/level3_tracker_free_space.toml` remain
unchanged.

Approved next training command:

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_004_speed_bin_balanced_generator_30m \
  --config level3_tracker_free_space.toml \
  --seed 26441 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m/v62d_004_speed_bin_balanced_generator_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_004_speed_bin_balanced_generator_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_004_speed_bin_balanced_generator_30m \
  --wandb-run-id v62d_004_speed_bin_balanced_generator_30m_20260627 \
  --jax-device gpu
```

## v62d_004 Result

Analysis:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_004_speed_bin_balanced_generator_30m_analysis.md
```

Decision:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_004_decision.md
```

Best checkpoint inside this candidate:

```text
lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m/v62d_004_speed_bin_balanced_generator_30m_step_005000000.pkl
```

It is not promoted. Under the same `speed_bin_balanced` eval distribution it
improves velocity versus v62c 7M by only `5.37%`, below the `10%-15%` promotion
threshold, and action delta worsens `3.42x`. Against the standing v62c 7M
default frontier, velocity is `4.63%` worse and action delta is `18.2x` worse.

| Metric | v62c 7M default | v62c 7M speed-bin | v62d_004 best |
|---|---:|---:|---:|
| reward | -4.8459 | -2.1434 | -2.0530 |
| command position error | 0.6573 | 0.2095 | 0.1958 |
| cross-track error | 0.5214 | 0.1786 | 0.1634 |
| command velocity error | 0.7397 | 0.8179 | 0.7740 |
| done mean | 0.00391 | 0.00000 | 0.00000 |
| action delta | 0.000006 | 0.000034 | 0.000116 |
| balanced score | -7.5365 | -3.4438 | -3.2704 |

Post-audit on the best checkpoint passed for action/logprob semantics:

```text
action_clipping=ok
action_sampling_logprob=ok
advantage_scale=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=3.11e-7
```

The failure is behavioral and critic-stability related, not an action-path bug.
The next candidate should keep `speed_bin_balanced` but test a narrower
value/return stabilization knob.

## v62d_005 Plan

Hypothesis:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_005_hypothesis.md
```

This candidate trains from scratch with:

```text
command_generator_profile=speed_bin_balanced
value_target_scale=10.0
command_vel_error_coef=default
num_minibatches=4
update_epochs=1
```

## v62d_005 Result

Analysis:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_005_speedbin_value_scale10_30m_analysis.md
```

Decision:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_005_decision.md
```

Best checkpoint inside this candidate:

```text
lsy_drone_racing/control/checkpoints/v62d_005_speedbin_value_scale10_30m/v62d_005_speedbin_value_scale10_30m_step_015000000.pkl
```

It is not promoted. It improves critic/value diagnostics and spatial tracking,
but velocity obedience and action smoothness regress badly.

| Metric | v62c 7M default | v62c 7M speed-bin | v62d_004 best | v62d_005 best |
|---|---:|---:|---:|---:|
| reward | -4.8459 | -2.1434 | -2.0530 | -2.5289 |
| command position error | 0.6573 | 0.2095 | 0.1958 | 0.2022 |
| cross-track error | 0.5214 | 0.1786 | 0.1634 | 0.1725 |
| command velocity error | 0.7397 | 0.8179 | 0.7740 | 0.9929 |
| done mean | 0.00391 | 0.00000 | 0.00000 | 0.00108 |
| action delta | 0.000006 | 0.000034 | 0.000116 | 0.011608 |
| balanced score | -7.5365 | -3.4438 | -3.2704 | -3.9707 |

Post-audit on the best checkpoint:

```text
action_clipping=ok
action_sampling_logprob=bad
advantage_scale=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=1.76e-6
```

The next candidate should stop Family A value scaling and test a PPO stabilizer
that changes temporal credit horizon while keeping reward semantics fixed.

## v62d_006 Plan

Hypothesis:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_006_hypothesis.md
```

This candidate changes rollout geometry, so support validation is required
before 30M training:

```text
1024 envs x 32 steps -> 256 envs x 128 steps
```

Keep:

```text
command_generator_profile=speed_bin_balanced
value_target_scale=1.0
command_vel_error_coef=default
action_distribution=tanh_squashed_gaussian
observation_layout=level3_reference_tracker_command_v3
no gate/aperture/race/finish/stage reward
```

## v62d_006 Support

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_006_longrollout_support.md
```

Support decision:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_006_support_decision.md
```

Checker result:

```text
ALL GREEN
```

Support smoke completed `262,144` steps with:

```text
num_envs=256
num_steps=128
actual_timesteps=262144
steady_state_steps_per_s=413322
action_clipping=ok
action_sampling_logprob=ok
stored_vs_env_logprob_abs_mean ~= 3.17e-7
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
```

The audit reports `advantage_scale=large` and `reward_scale=large`, which is
expected with the longer horizon and must be monitored during the 30M run. It is
not a support blocker because action/logprob, finite metrics, metadata, and
config boundaries passed.

Approved next command is the 30M command recorded in:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_006_hypothesis.md
```
