# v62c Tanh-Squashed Gaussian 10M Analysis

Date: 2026-06-27

## Purpose

Run the first bounded online-W&B v62c training chunk after formalizing the PPO
action distribution as:

```text
raw_action ~ Normal(mean, std)
env_action = tanh(raw_action)
logprob = Gaussian(raw_action) - log |det d tanh(raw_action) / d raw_action|
```

This tests whether the Brax/JAX clean reference-command tracker can learn with
the formal tanh-squashed action path. It is not a Level3 final success eval and
does not approve 60M+ maturation.

## Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62c_tanh_squashed_gaussian_10m \
  --config level3_tracker_free_space.toml \
  --seed 26310 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 10027008 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 1048576 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62c_tanh_squashed_gaussian_10m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62c_tanh_squashed_gaussian_10m \
  --wandb-run-id v62c_tanh_squashed_gaussian_10m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62c_tanh_squashed_gaussian_10m_20260627
```

## Artifacts

- Final checkpoint:
  `lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_final.pkl`
- Summary JSON:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62c_tanh_squashed_gaussian_10m_summary.json`
- Post-run audit JSON:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62c_tanh_squashed_gaussian_10m_post_audit.json`

These generated checkpoint/JSON artifacts remain ignored by git.

## Run Metadata

| Field | Value |
|---|---|
| lane | `v62c_tanh_squashed_gaussian_10m` |
| config | `level3_tracker_free_space.toml` |
| task | `reference_command_no_gate_reward` |
| observation layout | `level3_reference_tracker_command_v3` |
| obs dim | `56` |
| reward scope | `no gate/aperture/obstacle/race/finish/stage reward` |
| action distribution | `tanh_squashed_gaussian` |
| logprob mode | `tanh_squashed_gaussian_logprob_with_jacobian` |
| initial log std | `-2.0` |
| entropy coef | `0.0` |
| actual timesteps | `10,027,008` |

## Speed

| Metric | Value |
|---|---:|
| first update elapsed | `18.01s` |
| steady-state env steps/s | `1,304,949` |
| steady-state vs PyTorch fast path | `32.79x` |

The Brax/JAX speed route remains healthy after switching to tanh-squashed
Gaussian.

## Pre/Post Deterministic Eval

| Metric | Initial | Final | Delta | Direction |
|---|---:|---:|---:|---|
| reward mean | `-4.6670` | `-3.0376` | `+1.6293` | improved |
| command position error | `0.4990` | `0.4440` | `-0.0550` | improved |
| cross-track error | `0.4116` | `0.3254` | `-0.0861` | improved |
| done mean | `0.0064` | `0.0` | `-0.0064` | improved |
| command velocity error | `0.6070` | `0.7457` | `+0.1387` | worsened |
| action abs mean | `0.0122` | `0.0329` | `+0.0207` | increased |
| action delta penalty | `0.000006` | `0.000013` | `+0.000008` | worsened |

Summary flag:

```text
has_eval_learning_signal = true
```

This is enough to say the v62c JAX trainer can produce useful learning signal.
It is not enough to promote to long maturation because velocity tracking and
smoothness worsened.

## Last Training Batch

| Metric | Value |
|---|---:|
| action clip fraction | `0.0` |
| logprob/env consistency error | `3.15e-7` |
| approx KL | `0.00369` |
| clip fraction | `0.0402` |
| entropy | `-2.4421` |
| advantage mean/std | `-41.87 / 42.29` |
| value loss | `1766.03` |
| rollout reward mean | `-5.7186` |
| rollout position error | `0.8515` |
| rollout velocity error | `0.7236` |
| rollout cross-track error | `0.6725` |
| all finite | `1.0` |

The action/logprob path stayed clean, but the train-batch value/advantage
pressure remains a real diagnostic issue.

## Post-Run Checkpoint Audit

Command:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26311 \
  --num-envs 1024 \
  --num-steps 32 \
  --checkpoint lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_final.pkl \
  --action-distribution tanh_squashed_gaussian \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62c_tanh_squashed_gaussian_10m_post_audit.json \
  --jax-device gpu
```

Checkpoint audit verdicts:

| Check | Result |
|---|---|
| action clipping | `ok` |
| action sampling/logprob | `ok` |
| advantage scale | `ok` |
| initial/policy std | `ok` |
| reward scale | `ok` |

Key checkpoint audit values:

| Metric | Value |
|---|---:|
| policy std mean | `0.1314` |
| any-dim clipped fraction | `0.0` |
| stored-vs-env logprob abs mean | `3.18e-7` |
| reward mean | `-2.2649` |
| command position error | `0.2273` |
| command velocity error | `0.8709` |
| cross-track error | `0.1961` |
| advantage mean/std | `-14.31 / 5.66` |
| value mean | `-96.74` |
| return mean | `-111.05` |

This post-run audit is important: it makes the JAX/tanh PPO semantics look
healthy. The remaining problem is tracker behavior and value/velocity training,
not action clipping or logprob accounting.

## Interpretation

v62c answers the immediate concern:

```text
JAX/Brax trainer can learn under the formal tanh-squashed PPO action path.
```

The evidence:

- pre/post deterministic eval improved on reward, position, cross-track, and
  done rate;
- action clipping stayed `0.0`;
- stored logprob matched the tanh-bounded env action to about `3e-7`;
- final checkpoint audit passed action, std, reward, and advantage checks.

The open problems:

- velocity tracking worsened in deterministic eval;
- action magnitude and action-delta increased;
- training-batch value loss and raw advantages are still large;
- milestone checkpoints were saved but not yet ranked.

## Conclusion

Do not blame JAX as the primary bottleneck based on current evidence. v62c is a
valid learning backend.

Do not jump straight to 60M+ training either. The next useful step is a
milestone/value/velocity review:

1. evaluate saved `1M-9M` milestone checkpoints plus final;
2. identify whether an earlier checkpoint has better velocity/smoothness than
   final;
3. inspect W&B value loss, advantage, clip fraction, position/cross-track, and
   velocity curves;
4. decide between continuing v62c, changing value/return scaling, or tuning the
   command velocity reward.
