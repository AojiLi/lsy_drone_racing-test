# Launch v29 Revert-Reward Success-Churn Replay 5M

Decision: `launch_named_structural_lane`

Approved command class: exactly one bounded 5M train/evaluate screen through
`scripts/level3_ppo_loop.py`, followed by analyzer, three subagent reviews, and
a new main-agent decision packet before any further training.

## Rationale

Loop089 is rejected as a continuation path. It raised gate-conversion reward
numbers from loop088 4M, but validation-unseen hard eval regressed:

- success fell from 0.19 to 0.18;
- crash rose from 0.81 to 0.82;
- mean gates fell from 1.57 to 1.49;
- mean successful time moved from 6.846s to 7.002s.

The W&B/reward improvement did not convert to the hard evaluator, so v29 must
not continue loop089 or mature loop089 to 60M/90M.

The train-pool diagnostic on seeds `2300-2399` found success churn between
loop088 and loop089 without using validation or final seeds. v29 uses that
training-only evidence as a low-probability replay sampler while reverting the
rejected reward escalation.

## Approved Lane

Structural hypothesis:

`v29_revert_reward_success_churn_replay_5m`

Allowed implementation details:

- hard eval config: `config/level3_dr.toml`;
- training config: `level3_dr.toml`;
- initial checkpoint: loop088 4M;
- observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- controller: existing 2x256 Tanh MLP PPO;
- teacher retention: loop052 teacher, success24 retention dataset, beta `0.10`;
- reward numbers: revert to loop088/v28 values;
- track generator profile: `v29_train_pool_success_churn_replay`;
- replay seeds:
  `2301, 2321, 2330, 2331, 2335, 2343, 2352, 2353, 2355, 2361, 2364, 2370, 2374, 2381, 2383, 2384`;
- replay probability: `0.16`;
- checkpoint interval: 1M;
- milestone hard eval: 1M, 2M, 3M, 4M, 5M;
- W&B project: `ADR-PPO-Racing-Level3`;
- W&B entity: `aojili77-technical-university-of-munich`.

## Required Command Constraints

The next real training command must include:

- `--max-iterations 1`;
- `--wandb-enabled`;
- `--wandb-entity aojili77-technical-university-of-munich`;
- `--codex-autonomous-loop`;
- `--override-state-hold`;
- `--structural-hypothesis v29_revert_reward_success_churn_replay_5m`;
- `--approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_launch_v29_revert_reward_success_churn_replay_5m.md`;
- `--research-packet experiments/level3_ppo_loop/diagnostics/2026-06-22_v29_train_pool_success_churn_probe.md`.

Dry-run this exact command before launching.

## Explicitly Rejected Actions

- Do not continue loop089.
- Do not mature loop089 to 60M/90M.
- Do not change `config/level3_dr.toml`.
- Do not use `final_locked` seeds.
- Do not launch more than one train/evaluate iteration before analysis.
- Do not accept W&B reward improvement without hard-eval improvement.

## Post-Run Analysis Requirements

After v29 completes, run `scripts/analyze_level3_ppo_trial.py` with W&B online
access, then create exactly three reviews:

- evaluator metrics and checkpoint milestone review;
- W&B/PPO/retention diagnostics review;
- structure/research synthesis review.

The main agent must then write a new decision packet choosing exactly one of:
`stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`,
`change_reward_or_training_numbers`, or `launch_named_structural_lane`.
