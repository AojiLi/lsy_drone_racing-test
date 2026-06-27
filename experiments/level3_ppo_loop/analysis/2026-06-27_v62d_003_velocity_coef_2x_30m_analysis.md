# v62d_003 Velocity Coef 2x 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate `v62d_003_velocity_coef_2x_30m` in the high-budget generic
reference-tracker search.

Hypothesis:

```text
Increasing the generic ReferenceCommandReward velocity-error coefficient from
0.6 to 1.2 will improve commanded-speed obedience without changing the actor
observation, action distribution, race config, or gate/race reward semantics.
```

This is a bottom-tracker free-space command-following run, not a Level3 hard
eval.

## Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_003_velocity_coef_2x_30m \
  --config level3_tracker_free_space.toml \
  --seed 26431 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_003_velocity_coef_2x_30m/v62d_003_velocity_coef_2x_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_003_velocity_coef_2x_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-vel-error-coef 1.2 \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_003_velocity_coef_2x_30m \
  --wandb-run-id v62d_003_velocity_coef_2x_30m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_003_velocity_coef_2x_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `1.286M env steps/s`.

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_003_velocity_coef_2x_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_003_velocity_coef_2x_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_003_velocity_coef_2x_30m_best_audit.json
```

Milestones were evaluated at `5M / 10M / 15M / 20M / 25M / 30M / final` with:

```text
config: level3_tracker_free_space.toml
seed: 26310
num_envs: 1024
num_steps: 32
eval_rollouts: 16
action_distribution: tanh_squashed_gaussian
reward_coefficients: {"vel_error_coef": 1.2}
```

`reward_mean` therefore uses the candidate's doubled velocity coefficient.
Promotion is judged primarily by behavior metrics because reward scale is no
longer directly comparable to v62c.

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M baseline | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| 5M | -6.2208 | 0.6527 | 0.5359 | 0.9429 | 0.00586 | 0.000025 | -9.0960 |
| 10M | -6.1301 | 0.6111 | 0.4951 | 0.9728 | 0.00586 | 0.000033 | -8.8831 |
| 15M | -5.4144 | 0.6722 | 0.5364 | 0.7644 | 0.00391 | 0.000016 | -8.1758 |
| 20M | -5.1643 | 0.6381 | 0.5022 | 0.7219 | 0.00391 | 0.000050 | -7.7744 |
| 25M | -5.9094 | 0.6232 | 0.5147 | 0.8819 | 0.00586 | 0.000126 | -8.6481 |
| 30M | -5.6168 | 0.7259 | 0.5798 | 0.7510 | 0.00391 | 0.000089 | -8.5407 |
| final | -5.6168 | 0.7259 | 0.5798 | 0.7510 | 0.00391 | 0.000089 | -8.5407 |

Balanced score is the same review heuristic used for prior v62d candidates:

```text
reward
- 2.0 * position_error
- 1.5 * cross_track_error
- 0.75 * velocity_error
- 10.0 * done_mean
- 2.0 * action_delta_penalty
```

## Best Checkpoint

Best checkpoint inside v62d_003:

```text
20M
lsy_drone_racing/control/checkpoints/v62d_003_velocity_coef_2x_30m/v62d_003_velocity_coef_2x_30m_step_020000000.pkl
```

It is best by balanced score, behavior score, and command velocity error inside
this candidate. Against the v62c 7M frontier:

| Metric | v62c 7M | v62d_003 20M | Change |
|---|---:|---:|---:|
| command position error | 0.6573 | 0.6381 | 2.9% better |
| cross-track error | 0.5214 | 0.5022 | 3.7% better |
| command velocity error | 0.7397 | 0.7219 | 2.4% better |
| done mean | 0.00391 | 0.00391 | unchanged |
| action delta | 0.000006 | 0.000050 | 7.9x worse |
| reward | -4.8459 | -5.1643 | worse |
| balanced score | -7.5365 | -7.7744 | worse |

The candidate does not meet the promotion threshold because velocity improves
by only `2.4%`, far below the required `10%-15%`, and action smoothness
materially worsens.

## Post-Run Audit

Best checkpoint audit:

```text
checkpoint: v62d_003...step_020000000.pkl
sample_clip_fraction: 0.0
stored_vs_env_logprob_abs_mean: 3.10e-7
action_sampling_logprob: ok
action_clipping: ok
advantage_scale: ok
reward_scale: ok
initial_std: ok
advantage mean/std: -10.70 / 4.75
reward abs mean/p95: 2.835 / 3.590
```

The action distribution and log-prob path are healthy. The candidate failure is
not the old clipped-action mismatch and not a tanh-squash bookkeeping bug.

Final training-batch PPO diagnostics:

```text
approx_kl: 0.00333
clip_fraction: 0.02893
entropy: -2.7874
value_loss: 583.43
advantages mean/std: -20.94 / 27.08
returns mean/std: -305.49 / 27.08
explained_variance: 0.000065
all_finite: 1.0
```

The PPO update is finite with low KL/clip pressure, but the critic remains
nearly flat relative to return variation. That is a continuing secondary
blocker, not the main v62d_003 failure.

## Three-Reviewer Synthesis

Reviewer 1, tracker eval metrics:

```text
Reject v62d_003. Best milestone is 20M, but velocity improves only 2.4% and
action delta is 7.9x worse than v62c 7M. Final/30M drifts down.
```

Reviewer 2, W&B/PPO diagnostics:

```text
Action/logprob and clipping are clean. KL/clip are not unstable. Reward scale is
ok in the best audit, but the value function remains underfit. More velocity
weight alone did not create real velocity obedience.
```

Reviewer 3, structure/research:

```text
Switch to Family C generator velocity distribution. v62d_003 shows blunt
velocity reward weighting is insufficient; the next candidate should change the
training generator so speed bins, brake ramps, low-speed-through, and recovery
segments are represented more clearly.
```

## Conclusion

Decision: reject `v62d_003`; do not promote it.

Current frontier remains:

```text
v62c 7M
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

Next candidate should be:

```text
v62d_004_speed_bin_balanced_generator
Family C: generator velocity distribution
```

Keep:

```text
action_distribution=tanh_squashed_gaussian
value_target_scale=1.0
num_minibatches=4
update_epochs=1
command_vel_error_coef default, not 1.2
actor observation level3_reference_tracker_command_v3
no gate/aperture/race/finish/stage rewards
unchanged config/level3.toml
```
