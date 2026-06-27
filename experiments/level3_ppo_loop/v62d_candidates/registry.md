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
