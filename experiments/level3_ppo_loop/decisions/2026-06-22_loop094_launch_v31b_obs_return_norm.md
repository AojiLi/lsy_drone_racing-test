# Loop094 Decision: Implement v31b Observation/Return Normalization

Decision: `launch_named_structural_lane`

Status: approved for implementation and dry-run of the next named structural
lane. Do not launch v31b training until focused support tests and a dry-run pass.

## Scope

Final acceptance remains `config/level3.toml` with success rate `>=0.60` and
mean successful time `<=7.0s`.

Do not modify Level3 track geometry or randomization. `config/level3_dr.toml`
remains training-only robustness context, not the final gate.

## Loop094 Evidence

Loop094 tested `v31a_longer_rollout_clean_ppo_5m`:

- v5 deployed observation;
- loop052 reward and PPO numbers;
- corrected v30 episode/reset semantics;
- rollout geometry `256 envs x 128 steps`;
- loop052 final initialization;
- hard eval on `config/level3.toml` validation_unseen seeds 101-200.

Best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m_step_004000000.ckpt`

Metrics:

- success: `19/100`;
- mean successful time: `6.875789473684211s`;
- crash: `81/100`;
- timeout: `0/100`;
- mean gates: `1.55`;
- final checkpoint regressed to `13/100`.

Compared with loop093, v31a improved success by `+2pp`, crash by `-2pp`, and
time by about `0.17s`, but mean gates stayed flat. This is a weak positive
screen, not a promotion.

## Reviewer Synthesis

Evaluator metrics:

- v31a is weakly positive and possibly eligible for cautious maturation from
  the 4M checkpoint;
- milestone-aware checkpoint selection is required because final regressed.

W&B/PPO diagnostics:

- PPO did not collapse;
- update pressure is low: KL and clip fraction remain tiny;
- reward curves and hard eval show only weak conversion.

Structure/research:

- v31a completed the clean longer-rollout baseline stage;
- the next framework priority is observation/return normalization, not reward
  numbers or speed optimization;
- keep `256 x 128` as the clean baseline geometry.

## Decision

Do not launch an immediate long v31a maturation run.

Implement the next named structural lane:

`v31b_obs_return_norm_clean_ppo_5m`

Required support:

- actor observation RunningMeanStd;
- frozen eval-time normalization statistics;
- checkpoint save/load for normalization state;
- critic/return running scale or equivalent value-target normalization;
- compatibility handling for warm-starting checkpoints without normalization
  metadata;
- focused tests for save/load and deterministic inference/eval behavior.

Initial v31b training plan after support passes:

- train config: `level3.toml`;
- hard eval config: `level3.toml`;
- actor observation: v5;
- rollout: `256 envs x 128 steps`;
- reward/PPO numbers: loop052 values initially;
- initial checkpoint: prefer loop094 4M only if compatibility is explicit and
  tested; otherwise use loop052 final;
- horizon: 5M screen with 1M milestone checkpoints;
- W&B project: `ADR-PPO-Racing-Level3`.

## Rejected Next Moves

- Do not modify `config/level3.toml`.
- Do not tune for speed while success is below 50%.
- Do not accept W&B reward curves without hard eval.
- Do not run reward-number search before the v31b support decision unless
  implementation is blocked.
- Do not assume final checkpoint is best.

## Next Command After Implementation

This packet intentionally does not provide a training command yet. The next
work is code support plus dry-run:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v31b_obs_return_norm_clean_ppo_5m \
  --override-state-hold \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop094_launch_v31b_obs_return_norm.md
```
