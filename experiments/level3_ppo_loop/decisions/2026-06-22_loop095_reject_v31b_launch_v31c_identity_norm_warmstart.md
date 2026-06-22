# Loop095 Decision: Reject From-Scratch v31b, Launch v31c Identity-Norm Warm Start

Decision: `launch_named_structural_lane`

Status: approved for implementation and dry-run of the next named structural
lane. Do not launch v31c training until zero-update identity-normalization
parity against loop094 4M passes on `config/level3.toml` validation_unseen
seeds 101-200.

## Scope

Final acceptance remains `config/level3.toml` with success rate `>=0.60` and
mean successful time `<=7.0s`.

Do not modify Level3 track geometry or randomization. `config/level3_dr.toml`
remains training-only robustness context, not the final gate.

## Loop095 Evidence

Loop095 tested `v31b_obs_return_norm_clean_ppo_5m`:

- v5 deployed observation;
- loop052 reward and PPO numbers;
- corrected v30 episode/reset semantics;
- rollout geometry `256 envs x 128 steps`;
- actor observation RunningMeanStd;
- critic return/value normalization;
- from-scratch initialization;
- hard eval on `config/level3.toml` validation_unseen seeds 101-200.

Best loop095 checkpoint was only best because all checkpoints failed:

- success: `0/100`;
- mean successful time: none;
- crash: `96/100`;
- timeout: `4/100`;
- mean gates: `0.0`;
- failures by target gate: `{"0": 100}`.

Across 1M, 2M, 3M, 4M, and final, success stayed `0%`; mean gates stayed
`0.0` except final `0.01`.

Current best remains loop094/v31a 4M:

`lsy_drone_racing/control/checkpoints/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m_step_004000000.ckpt`

Metrics:

- success: `19/100`;
- mean successful time: `6.875789473684211s`;
- crash: `81/100`;
- mean gates: `1.55`.

## Reviewer Synthesis

Evaluator metrics:

- reject v31b maturation;
- v31b regressed by `-19pp` success and `-1.55` mean gates versus loop094;
- action/tilt metrics look under-actuated, not like a promising immature policy.

W&B/PPO diagnostics:

- value loss scale improved under return normalization;
- PPO did not numerically collapse;
- W&B gate/finish signals did not convert: `race/passed_gate_rate=0`,
  `race/finished_rate=0`;
- explicit normalization health metrics should be logged before relying on the
  normalization lane.

Structure/research:

- loop095 rejects the from-scratch v31b start condition, not necessarily the
  normalization roadmap;
- the next test should preserve the working loop094 behavioral prior and add
  identity actor-observation normalization in a parity-checked way.

## Decision

Reject `v31b_obs_return_norm_clean_ppo_5m` as a continuation target. Do not
mature it to 30M/60M.

Implement the next named structural lane:

`v31c_warmstart_identity_norm_clean_ppo_5m`

Required support:

- create or load a warm-start checkpoint from loop094 4M with identity
  actor-observation normalization metadata;
- zero-update deterministic hard-eval parity against loop094 4M before training;
- return/value normalization initialized compatibly with the warm-start critic;
- W&B logging for normalization health metrics;
- 5M screen only after parity passes, with 1M milestone hard evals.

Initial v31c training plan after parity passes:

- train config: `level3.toml`;
- hard eval config: `level3.toml`;
- actor observation: v5;
- rollout: `256 envs x 128 steps`;
- reward/PPO numbers: loop052 values initially;
- initial checkpoint: loop094 4M identity-normalized warm-start checkpoint;
- horizon: 5M screen with 1M milestone checkpoints;
- W&B project: `ADR-PPO-Racing-Level3`.

## Rejected Next Moves

- Do not continue from-scratch v31b.
- Do not tune speed while success is below 50%.
- Do not launch privileged critic/curriculum/PLR/GRU until the normalization
  compatibility question is resolved or explicitly rejected.
- Do not modify `config/level3.toml`.
- Do not accept W&B reward curves without hard eval.

## Next Command After Implementation

The next work is code support plus dry-run/parity. Training command is withheld
until parity passes.

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v31c_warmstart_identity_norm_clean_ppo_5m \
  --override-state-hold \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_095_structural_v31b_obs_return_norm_clean_ppo_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop095_reject_v31b_launch_v31c_identity_norm_warmstart.md
```
