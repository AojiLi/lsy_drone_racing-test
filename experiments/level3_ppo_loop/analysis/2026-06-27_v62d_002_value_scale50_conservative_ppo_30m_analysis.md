# v62d_002 Value Scale 50 Conservative PPO 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate `v62d_002` in the high-budget generic reference-tracker
search.

This is not a Level3 hard evaluation. It is a tracker free-space
command-following candidate test.

## Candidate

```text
id: v62d_002
family: D_PPO_stabilizer
lane: v62d_002_value_scale50_conservative_ppo_30m
train start: from scratch
timesteps: 30,015,488
rollout geometry: 1024 envs x 32 steps
action distribution: tanh_squashed_gaussian
value_target_scale: 50.0
num_minibatches: 4
update_epochs: 1
W&B: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_002_value_scale50_conservative_ppo_30m_20260627
```

Hard boundaries were respected:

- `config/level3.toml` unchanged;
- `config/level3_tracker_free_space.toml` unchanged;
- actor observation stayed `level3_reference_tracker_command_v3`;
- reward stayed no-gate/no-aperture/no-race/no-finish/no-stage;
- action distribution stayed `tanh_squashed_gaussian`;
- candidate trained from scratch, not from v62c.

## Training

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_002_value_scale50_conservative_ppo_30m \
  --config level3_tracker_free_space.toml \
  --seed 26421 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_002_value_scale50_conservative_ppo_30m/v62d_002_value_scale50_conservative_ppo_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_002_value_scale50_conservative_ppo_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --value-target-scale 50.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_002_value_scale50_conservative_ppo_30m \
  --wandb-run-id v62d_002_value_scale50_conservative_ppo_30m_20260627 \
  --jax-device gpu
```

Runtime stayed fast:

```text
steady-state steps/s: 1,288,563
steady-state vs PyTorch fast path: 32.38x
```

## Eval Protocol

Generated local artifacts:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_002_value_scale50_conservative_ppo_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_002_value_scale50_conservative_ppo_30m_milestone_eval.csv
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
| 5M | 5,013,504 | -6.9258 | 0.4066 | 0.3439 | 0.7721 | 0.01615 | 0.00276 | -9.0010 |
| 10M | 10,027,008 | -9.5532 | 0.3169 | 0.2899 | 1.2991 | 0.02647 | 0.01282 | -11.8864 |
| 15M | 15,007,744 | -10.4474 | 0.2837 | 0.2548 | 1.3302 | 0.03100 | 0.01977 | -12.7442 |
| 20M | 20,021,248 | -10.3419 | 0.2762 | 0.2526 | 1.2751 | 0.03094 | 0.03243 | -12.6039 |
| 25M | 25,001,984 | -9.8393 | 0.2659 | 0.2481 | 1.1847 | 0.02928 | 0.02769 | -11.9799 |
| 30M | 30,015,488 | -9.4275 | 0.3862 | 0.3277 | 1.2421 | 0.02509 | 0.01610 | -11.9061 |
| final | 30,015,488 | -9.4275 | 0.3862 | 0.3277 | 1.2421 | 0.02509 | 0.01610 | -11.9061 |

Balanced score is the same review-only heuristic used in the v62c and v62d_001
milestone reviews.

## Best Checkpoint

Best v62d_002 checkpoint by balanced score and by velocity:

```text
5M
lsy_drone_racing/control/checkpoints/v62d_002_value_scale50_conservative_ppo_30m/v62d_002_value_scale50_conservative_ppo_30m_step_005000000.pkl
```

It is not promotable. It improves spatial tracking versus v62c 7M, but it fails
the actual promotion threshold:

```text
velocity: 0.7721 vs 0.7397 baseline
done: 0.01615 vs 0.00391 baseline
reward: -6.9258 vs -4.8459 baseline
action_delta: 0.00276 vs 0.000006 baseline
balanced: -9.0010 vs -7.5365 baseline
```

The 25M checkpoint is best for position and cross-track, but it is worse on the
core command-following behavior:

```text
25M position error: 0.2659
25M cross-track: 0.2481
25M velocity error: 1.1847
25M done mean: 0.02928
25M action_delta: 0.02769
```

That is the same basic failure mode as v62d_001, just less extreme.

## Audit

Best-checkpoint audit:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_002_value_scale50_conservative_ppo_30m_best_audit.json
```

Checkpoint `5M` audit verdicts:

| Check | Verdict |
|---|---|
| action clipping | `ok` |
| action sampling/logprob | `ok` |
| advantage scale | `ok` |
| initial/std policy std | `ok` |
| reward scale | `ok` |
| stored-vs-env logprob abs mean | `7.10e-7` |
| value target scale | `50.0` |

The audit rules out the main action-path bug class. The candidate failed
behaviorally: it learned better spatial chasing than v62c, but it did not obey
commanded velocity as well as the v62c 7M frontier.

## PPO Diagnostics

`value_target_scale=50.0` still fixed critic magnitude pressure:

```text
final value_loss: 0.0221
final explained_variance: 0.4827
final raw values_mean: -265.2706
final returns_mean: -265.4022
final scaled values_mean: -5.3054
final value_targets_mean: -5.3080
```

But conservative PPO update pressure did not restore v62c-like update behavior:

```text
v62d_002 final approx_kl: 0.0210
v62d_002 final clip_fraction: 0.2786
v62c final approx_kl: about 0.00369
v62c final clip_fraction: about 0.0402
```

Final deterministic eval also shows the behavioral tradeoff:

```text
position error: 1.1155 -> 0.3764
cross-track: 0.7863 -> 0.3200
velocity error: 0.6474 -> 1.2424
done mean: 0.00285 -> 0.02545
action_abs: 0.0160 -> 0.3042
reward: -6.2076 -> -9.4719
```

## Reviewer Synthesis

Three post-run reviewers agreed:

- `tracker_eval_metrics`: select 5M as best inside v62d_002, but reject
  promotion because velocity, done, action_delta, reward, and balanced score
  regress versus v62c 7M.
- `tracker_wandb_ppo`: action/logprob path is healthy and value scale is no
  longer the main blocker, but KL/clip, action magnitude, velocity error, and
  done rate still drift.
- `tracker_structure_research`: close the value-scale isolation question and
  switch to a generic velocity-obedience reward-number candidate.

## Conclusion

Do not promote `v62d_002`.

Keep v62c 7M as the current comparison frontier checkpoint.

The next candidate should switch to Family B:

```text
v62d_003_velocity_coef_2x
```

Proposed single knob:

```text
ReferenceCommandReward vel_error_coef: 0.6 -> 1.2
```

Return to v62c-style value/update defaults for the next single-family test:

```text
value_target_scale=1.0
num_minibatches=4
update_epochs=1
1024 envs x 32 steps
tanh_squashed_gaussian
```

Because this changes reward numbers, run builder/checker validation before
launching training. The change must remain generic command tracking only:
no gate, aperture, obstacle, planner-phase, race, finish, or stage reward/input.
