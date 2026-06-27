# v62d_001 Value Target Scale 50 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate `v62d_001` in the high-budget generic reference-tracker
search.

This is not a Level3 hard evaluation. It is a tracker free-space
command-following candidate test.

## Candidate

```text
id: v62d_001
family: A_value_return_stabilization
lane: v62d_001_value_target_scale50_30m
train start: from scratch
timesteps: 30,015,488
rollout geometry: 1024 envs x 32 steps
action distribution: tanh_squashed_gaussian
value_target_scale: 50.0
W&B: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_001_value_target_scale50_30m_20260627
```

Hard boundaries were respected:

- `config/level3.toml` unchanged;
- `config/level3_tracker_free_space.toml` unchanged;
- actor observation stayed `level3_reference_tracker_command_v3`;
- reward stayed no-gate/no-aperture/no-race/no-finish/no-stage;
- action distribution stayed `tanh_squashed_gaussian`.

## Training

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_001_value_target_scale50_30m \
  --config level3_tracker_free_space.toml \
  --seed 26411 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 8 \
  --update-epochs 4 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_001_value_target_scale50_30m/v62d_001_value_target_scale50_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_001_value_target_scale50_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --value-target-scale 50.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_001_value_target_scale50_30m \
  --wandb-run-id v62d_001_value_target_scale50_30m_20260627 \
  --jax-device gpu
```

Runtime stayed fast:

```text
steady-state steps/s: 1,005,991
steady-state vs PyTorch fast path: 25.28x
```

## Eval Protocol

Generated local artifacts:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_001_value_target_scale50_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_001_value_target_scale50_30m_milestone_eval.csv
```

Protocol:

| Field | Value |
|---|---:|
| config | `level3_tracker_free_space.toml` |
| seed | `26310` |
| num envs | `1024` |
| num steps | `32` |
| eval rollouts | `16` |
| action distribution | `tanh_squashed_gaussian` |

Baseline is the v62c 7M checkpoint:

```text
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

## Milestone Results

| checkpoint | actual step | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M baseline | 7,340,032 | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| 5M | 5,013,504 | -9.7541 | 0.2851 | 0.2633 | 1.2018 | 0.02903 | 0.01675 | -11.9443 |
| 10M | 10,027,008 | -10.5905 | 0.2638 | 0.2471 | 1.3048 | 0.03266 | 0.02362 | -12.8411 |
| 15M | 15,007,744 | -10.9814 | 0.2583 | 0.2423 | 1.3519 | 0.03416 | 0.02781 | -13.2726 |
| 20M | 20,021,248 | -11.1196 | 0.2562 | 0.2397 | 1.3648 | 0.03465 | 0.02759 | -13.4170 |
| 25M | 25,001,984 | -11.1267 | 0.2558 | 0.2396 | 1.3611 | 0.03472 | 0.02728 | -13.4203 |
| 30M | 30,015,488 | -10.9436 | 0.2574 | 0.2409 | 1.3399 | 0.03401 | 0.02903 | -13.2228 |
| final | 30,015,488 | -10.9436 | 0.2574 | 0.2409 | 1.3399 | 0.03401 | 0.02903 | -13.2228 |

Balanced score is the same review-only heuristic used in the v62c milestone
review.

## Best Checkpoint

Best v62d_001 checkpoint by balanced score and by velocity:

```text
5M
lsy_drone_racing/control/checkpoints/v62d_001_value_target_scale50_30m/v62d_001_value_target_scale50_30m_step_005000000.pkl
```

But it is not promotable. It improves spatial tracking versus v62c 7M but
fails the actual promotion threshold:

```text
velocity: 1.2018 vs 0.7397 baseline
done: 0.02903 vs 0.00391 baseline
reward: -9.7541 vs -4.8459 baseline
action_delta: 0.01675 vs 0.000006 baseline
```

## Audit

Best-checkpoint audit:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_001_value_target_scale50_30m_best_audit.json
```

Checkpoint `5M` audit verdicts:

| Check | Verdict |
|---|---|
| action clipping | `ok` |
| action sampling/logprob | `ok` |
| advantage scale | `ok` |
| initial/std policy std | `ok` |
| reward scale | `large` |
| stored-vs-env logprob abs mean | `9.04e-7` |
| value target scale | `50.0` |

This rules out the main action-path bug class. The candidate failed
behaviorally: the policy learned a high-action spatial chase instead of
obeying commanded velocity.

## PPO Diagnostics

`value_target_scale=50.0` did solve critic scale pressure:

```text
final value_loss: 0.0006676
final explained_variance: 0.8662
final raw advantage mean/std: -0.1336 / 1.8043
final raw values_mean: -256.9093
final returns_mean: -257.0429
final scaled values_mean: -5.1382
final value_targets_mean: -5.1409
```

But policy update pressure and action strength rose:

```text
final approx_kl: 0.02150
final clip_fraction: 0.2741
entropy: -2.3299 -> -5.9083
final action_abs_mean: 0.5120
final action_delta: 0.02895
```

Important confounder: this run changed PPO update pressure at the same time as
value target scaling:

```text
v62c: 4 minibatches, 1 update epoch
v62d_001: 8 minibatches, 4 update epochs
```

Therefore v62d_001 does not prove value target scaling is bad by itself. It
proves that this combination produces an aggressive spatial chaser that fails
velocity obedience.

## Conclusion

Do not promote `v62d_001`.

Keep v62c 7M as the comparison baseline/frontier checkpoint.

The next candidate should isolate the confounder by combining
`value_target_scale=50.0` with conservative PPO update pressure matching v62c:

```text
v62d_002_value_scale50_conservative_ppo
--num-minibatches 4
--update-epochs 1
```

Only if that still sacrifices velocity should the search move to generic
velocity-obedience reward numbers.

