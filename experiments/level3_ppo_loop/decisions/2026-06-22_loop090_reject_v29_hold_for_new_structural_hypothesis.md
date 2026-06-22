# Reject loop090/v29 and Hold for New Structural Hypothesis

Decision: `hold_for_more_analysis`

Status: target not met. Do not launch another training chunk from this decision.

## Verdict

Reject `v29_revert_reward_success_churn_replay_5m` as a continuation lane.

Do not continue loop090, do not mature it toward 60M/90M, and do not launch
another automatic reward-number tweak from this state.

## Hard-Eval Evidence

Hard eval stayed on unchanged `config/level3_dr.toml`; no `final_locked` seeds
were used.

Best loop090 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_step_003000000.ckpt`

| Run | Best checkpoint | Success | Crash | Mean Gates | Mean Successful Time |
| --- | --- | ---: | ---: | ---: | ---: |
| loop052 anchor | final | 0.20 | 0.80 | 1.47 | 6.858s |
| loop088 | 4M | 0.19 | 0.81 | 1.57 | 6.846s |
| loop089 | 2M | 0.18 | 0.82 | 1.49 | 7.002s |
| loop090 | 3M | 0.14 | 0.86 | 1.39 | 6.720s |

Loop090 is faster among the few successes, but success rate, crash rate, and
mean gates all regress. This is not acceptable for the Level3 target.

## W&B/PPO Evidence

W&B/PPO diagnostics do not show a broken teacher-retention implementation or
obvious PPO optimizer blow-up:

- `retention/sampled_batch_size` stayed at `512`;
- `losses/teacher_kl` moved from about `1.033` to `0.710`;
- `retention/teacher_agreement` improved from about `0.861` to `0.892`;
- `losses/approx_kl` stayed near `0.004`;
- `losses/clipfrac` stayed near `0.006`.

The failure is conversion: reward and retention signals did not produce better
hard-eval gate progress.

## Behavior Diagnostic

The follow-up diagnostic strengthens the rejection:

- Validation loop090 lost 8 loop088 successes and gained only 3.
- Validation loop090 lost 6 loop089 successes and gained only 2.
- Validation loop090 lost 9 loop052-anchor successes and gained only 3.
- At loop090 best, all 86 validation failures are `bounds_or_ground`.
- On the 16 train-pool replay source seeds, success dropped to `7/16`, versus
  `10/16` for loop088 and `14/16` for loop089.

This means v29 did not merely fail validation generalization; it also failed to
preserve the replay-source behavior it was designed to retain.

## Subagent Consensus

All three required reviewers recommend hold:

- evaluator metrics: hold, do not mature loop090;
- W&B/PPO diagnostics: hold, W&B reward did not convert;
- structure/research synthesis: hold, reject v29 and require a fresh named
  structural/training hypothesis before further training.

## Required Next Work

Before another training chunk, write a new approved hypothesis packet. The next
candidate should be a fresh named structural or training-structure lane, not a
longer v29 continuation.

That packet must explicitly state:

- why loop052/088/089/090 behavior suggests the new direction;
- whether it changes observation, controller, reward structure, PPO/training
  structure, replay/data curriculum, or network architecture;
- how it keeps `config/level3_dr.toml` unchanged for hard eval;
- why it does not use `final_locked` seeds;
- what hard-eval milestones will decide acceptance or rejection.

## Rejected Actions

- Continue loop090.
- Mature loop090 to 60M/90M.
- Continue loop089.
- Launch another automatic reward-number tweak without a new packet.
- Modify `config/level3_dr.toml`.
- Use `final_locked` seeds for tuning, replay, diagnostics, or lane selection.

## Artifacts

- Main analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_analysis.md`
- Evaluator review:
  `experiments/level3_ppo_loop/analysis/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_eval_subagent_review.md`
- W&B/PPO review:
  `experiments/level3_ppo_loop/analysis/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_wandb_ppo_subagent_review.md`
- Structure/research review:
  `experiments/level3_ppo_loop/analysis/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_structure_research_subagent_review.md`
- Behavior diagnostic:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop090_v29_rejection_behavior_diagnostic.md`
