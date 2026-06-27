# v62b Brax PPO Signal Fix 10M Run

Date: 2026-06-27

## Purpose

Run a narrow v62b fix before any reward tuning:

1. expose `initial_log_std` as a CLI/configured training parameter;
2. default it to `-2.0`;
3. lower entropy pressure;
4. make the PPO logprob correspond to the action actually executed by the env;
5. run a bounded 10M pre/post deterministic eval and inspect the result.

This remains the clean no-gate bottom-tracker lane:

```text
level3_reference_tracker_command_v3
reference_command_no_gate_reward
no gate/aperture/obstacle/race/finish/stage reward
```

## Code Changes

- `scripts/train_v60_brax_ppo_smoke.py`
  - default `--initial-log-std=-2.0`;
  - default `--ent-coef=0.0`;
  - stores the env-executed bounded action in the PPO batch;
  - computes stored logprob from the same env action;
  - logs action clipping and logprob consistency metrics.
- `scripts/train_v62_brax_reference_command_tracker.py`
  - inherits the fixed PPO rollout/update path;
  - default `--initial-log-std=-2.0`;
  - default `--ent-coef=0.0`;
  - records `initial_log_std`, `ent_coef`, and
    `action_logprob_mode=env_clipped_action_gaussian_logprob`.
- `scripts/audit_v62b_brax_ppo_signals.py`
  - audits stored logprob versus env-action logprob instead of only comparing
    raw-sample logprob to clipped-action proxy logprob.

## Pre-10M Signal Audit

Command:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26233 \
  --num-envs 1024 \
  --num-steps 32 \
  --initial-log-std-values=-2.0 \
  --skip-checkpoint \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62b_signal_fix_pre10m_audit.json \
  --jax-device gpu
```

Key result:

| Metric | Value |
|---|---:|
| std | `0.1353` |
| clipped dim fraction | `0.0` |
| any-action clipped fraction | `0.0` |
| stored-vs-env logprob abs mean | `0.0` |
| reward mean | `-2.3897` |
| reward abs p95 | `3.2988` |
| advantage mean/std | `-25.2293 / 9.2189` |

The action/logprob/std/reward checks were clean. The advantage mean remained
borderline by the audit threshold, but the oversize action/logprob mismatch
that blocked v62 was fixed.

## 10M Command

`10,027,008` steps were used so the run reaches at least 10M with the
`1024 envs x 32 steps` batch geometry.

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62b_brax_ppo_signal_fix_10m \
  --config level3_tracker_free_space.toml \
  --seed 26240 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 10027008 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 1048576 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62b_brax_ppo_signal_fix_10m/v62b_brax_ppo_signal_fix_10m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62b_brax_ppo_signal_fix_10m_summary.json \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62b_brax_ppo_signal_fix_10m \
  --wandb-run-id v62b_brax_ppo_signal_fix_10m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62b_brax_ppo_signal_fix_10m_20260627
```

## Artifacts

- Final checkpoint:
  `lsy_drone_racing/control/checkpoints/v62b_brax_ppo_signal_fix_10m/v62b_brax_ppo_signal_fix_10m_final.pkl`
- Summary JSON:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62b_brax_ppo_signal_fix_10m_summary.json`
- Post-run signal audit:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62b_signal_fix_post10m_audit.json`

Generated checkpoint/JSON artifacts remain ignored by git.

## Speed

| Metric | Value |
|---|---:|
| actual timesteps | `10,027,008` |
| steady-state env steps/s | `1,296,978` |
| steady-state vs PyTorch fast path | `32.59x` |

The Brax/JAX speed route remains viable.

## Pre/Post Deterministic Eval

| Metric | Initial | Final | Delta | Direction |
|---|---:|---:|---:|---|
| reward mean | `-4.1090` | `-2.7413` | `+1.3677` | improved |
| command position error | `0.5153` | `0.4006` | `-0.1146` | improved |
| cross-track error | `0.4351` | `0.2803` | `-0.1548` | improved |
| done mean | `0.00417` | `0.0` | `-0.00417` | improved |
| command velocity error | `0.5479` | `0.6811` | `+0.1332` | worsened |
| action delta penalty | `0.000005` | `0.000080` | `+0.000074` | worsened |

The summary flag was:

```text
has_eval_learning_signal = true
```

This is the first v62/Brax run where the bounded pre/post deterministic eval
improved after training.

## Last Training Batch Diagnostics

Final training batch subset:

| Metric | Value |
|---|---:|
| rollout action clip fraction | `0.0` |
| any-action clipped fraction | `0.0` |
| action logprob/env consistency error | `0.0` |
| approx KL | `0.00897` |
| clip fraction | `0.1331` |
| entropy | `-2.4397` |
| advantage mean/std | `-46.06 / 42.59` |
| value loss | `1962.39` |
| rollout reward mean | `-6.1402` |
| all finite | `1.0` |

The action/logprob/std fix held throughout training. However, the final rollout
still shows large raw advantages and value loss, so value/return scaling or
critic-target handling may still matter.

## Post-10M Signal Audit

Final checkpoint audit:

| Metric | Value |
|---|---:|
| checkpoint step | `10,027,008` |
| std | `0.1315` |
| clipped dim fraction | `0.0` |
| any-action clipped fraction | `0.0` |
| stored-vs-env logprob abs mean | `0.0` |
| advantage mean/std | `-14.3383 / 5.8348` |
| reward mean | `-2.2663` |
| reward abs p95 | `3.1108` |
| command position error | `0.2278` |
| command velocity error | `0.8750` |
| cross-track error | `0.1964` |

The final checkpoint passed the action/logprob, clipping, std, advantage, and
reward-scale audit verdicts.

## Interpretation

The narrow v62b fix worked for its intended target:

```text
action sampling/logprob consistency: fixed
initial std too large: fixed
entropy pressure: disabled
10M deterministic eval signal: positive
```

But this is not yet a tracker-stage pass:

- velocity tracking worsened in deterministic eval;
- action magnitude and action delta increased;
- final training-batch advantages/value loss remain large;
- no Level3 planner integration evaluation was run.

## Conclusion

The v62/Brax route is now worth continuing, but not by immediately tuning gate
or tracker reward numbers.

Recommended next work:

1. run a v62b milestone-checkpoint eval over the saved 1M-9M checkpoints plus
   final, because final may not be the best checkpoint;
2. inspect W&B curves for velocity error, value loss, advantage scale, and
   clip fraction;
3. if the best milestone still has velocity-error regression, consider a
   narrow value/return normalization or critic-target scaling fix before reward
   changes;
4. only after the PPO signal and value scale are stable should reward tuning be
   reconsidered.

## Boundaries

- `config/level3.toml` was not modified.
- `config/level3_tracker_free_space.toml` was not modified.
- No gate/aperture/race/finish/stage reward was added.
- No gate/obstacle/planner-phase actor input was added.
