# v29 Train-Pool Success-Churn Probe

Status: evidence packet for one bounded v29 screen. This packet does not by
itself prove that v29 will generalize.

## Scope

This packet uses only training-pool diagnostic seeds `2300-2399` to compare:

- loop088 4M:
  `lsy_drone_racing/control/checkpoints/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_step_004000000.ckpt`
- loop089 2M:
  `lsy_drone_racing/control/checkpoints/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m_step_002000000.ckpt`

No dev, validation, or `final_locked` seeds are used as replay seeds for the
proposed training lane. Hard acceptance must still be measured on unchanged
`config/level3_dr.toml`.

## Evidence

| Metric on train_pool_2300_2399 | loop088 4M | loop089 2M |
| --- | ---: | ---: |
| success rate | 0.10 | 0.14 |
| successes | 10 / 100 | 14 / 100 |
| crash rate | 0.90 | 0.86 |
| mean gates | 1.38 | 1.47 |
| mean successful time | 7.460s | 7.391s |
| gate0 failure rate | 0.35 | 0.31 |
| gate3 failure rate | 0.12 | 0.06 |

The validation diagnostic moved in the opposite direction: loop089 had lower
validation success than loop088 4M. That means the stronger gate reward
adjustment is not accepted as a general improvement. The train-pool comparison
is useful only as a source of training-only replay candidates.

## Success Churn Seeds

- loop088 successes:
  `2331, 2335, 2343, 2355, 2364, 2370, 2374, 2381, 2383, 2384`
- loop089 successes:
  `2301, 2321, 2330, 2335, 2352, 2353, 2355, 2361, 2364, 2370, 2374, 2381, 2383, 2384`
- kept successes:
  `2335, 2355, 2364, 2370, 2374, 2381, 2383, 2384`
- loop088 successes lost by loop089:
  `2331, 2343`
- loop089 successes gained from loop088 failures:
  `2301, 2321, 2330, 2352, 2353, 2361`

Proposed v29 replay seed set:

`2301, 2321, 2330, 2331, 2335, 2343, 2352, 2353, 2355, 2361, 2364, 2370, 2374, 2381, 2383, 2384`

The replay probability is intentionally low (`0.16`) because loop089 improved
this train-pool slice but regressed on validation. v29 should test whether a
small amount of training-only success-churn replay can preserve and combine
behavior without importing loop089's rejected reward escalation.

## v29 Hypothesis

Launch one named structural lane:

`v29_revert_reward_success_churn_replay_5m`

Constraints:

- Start from loop088 4M, not loop089 2M.
- Revert reward numbers to loop088/v28 values.
- Keep v8 local gate-corridor observation.
- Keep 2x256 MLP PPO controller.
- Keep loop052 teacher checkpoint and success24 retention dataset.
- Use `v29_train_pool_success_churn_replay` only as a training sampler.
- Evaluate checkpoints on unchanged `config/level3_dr.toml`.
- Do not use `final_locked` seeds.

## Artifacts

- Train-pool summary CSV:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop088_vs_loop089_train_pool_2300_2399_summary.csv`
- Train-pool episodes CSV:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop088_vs_loop089_train_pool_2300_2399_episodes.csv`
- Validation behavior diagnostic:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop088_vs_loop089_behavior_diagnostic.md`
