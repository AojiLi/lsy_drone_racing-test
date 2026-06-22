# Loop095 v31b Structure/Research Synthesis Review

## Key Finding

Loop095 rejects the from-scratch v31b start condition, not the full
observation/return-normalization roadmap. The hard-eval result is too poor to
mature: `0/100` success, no successful time, `96%` crash at the best checkpoint,
and essentially no gate progress. The state best remains loop094/v31a 4M at
`19/100`, mean successful time `6.8758s`, crash `81%`, mean gates `1.55`.

## Evidence

Loop095 started from scratch with v5 observations, `256 x 128` rollout geometry,
actor observation normalization, and return/value normalization. Across
milestones it never converted: 1M and 2M had mean gates `0.0`; final reached
only `0.01`; success stayed `0%`.

Compared with loop094/v31a, loop095 regressed by `-19pp` success, `+15pp`
crash, and `-1.55` mean gates. W&B also shows no gate/finish conversion:
`race/passed_gate_rate=0`, `race/finished_rate=0`, low explained variance, and
weak policy movement. Evaluator summaries show much smaller action/tilt
magnitudes than v31a, consistent with a normalized from-scratch policy failing
to acquire even gate 0.

The framework packet still ranks observation/return normalization before
privileged critic, curriculum, PLR, GRU, reward-number search, or speed tuning.
But loop095 did not test normalization as an improvement to the existing best
policy; it discarded the only working behavioral prior.

## Recommended Next Action

`launch_named_structural_lane`: `v31c_warmstart_identity_norm_clean_ppo_5m`

Use loop094/v31a 4M as the initial checkpoint and add warm-start-compatible
normalization with identity actor-observation stats at initialization, so the
normalized actor preserves raw-checkpoint behavior before learning. Keep
`config/level3.toml` unchanged, keep v5 observations, loop052 reward/PPO
numbers, and `256 envs x 128 steps`.

## Required Packet Or Command

Write a decision packet approving `v31c_warmstart_identity_norm_clean_ppo_5m`.
It should require zero-update deterministic action/eval parity against loop094
4M before training, then a 5M screen with 1M milestone hard evals on
`config/level3.toml`.

## Risk / Rollback Condition

If identity-normalized warm start cannot reproduce loop094 4M behavior before
training, hold for normalization compatibility debugging. If it reproduces
parity but loses the v31a frontier after early milestones, reject normalization
for now and roll back to loop094/v31a best before moving further down the
roadmap.
