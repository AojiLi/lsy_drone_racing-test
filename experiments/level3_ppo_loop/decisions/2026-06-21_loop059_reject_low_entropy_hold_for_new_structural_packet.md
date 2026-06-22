# Main-Agent Decision After Loop059

Date: 2026-06-21

## Decision

`hold_for_more_analysis`

## Trial

`level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m`

## Evidence

Analysis:

`experiments/level3_ppo_loop/analysis/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m_analysis.md`

Subagent reviews:

`experiments/level3_ppo_loop/analysis/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m_subagent_reviews.md`

W&B run:

https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m

## Hard-Eval Result

Loop059 best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m_final.ckpt`

Metrics:

- Success rate: `0.10`
- Mean successful time: `7.13s`
- Crash rate: `0.90`
- Mean gates: `1.20`
- Target met: `false`

Current global best remains loop052:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Global-best metrics:

- Success rate: `0.20`
- Mean successful time: `6.975s`
- Crash rate: `0.80`
- Mean gates: `1.40`
- Target met: `false`

## Rationale

Loop059 tested one isolated training-structure change from loop052:

- `ent_coef: 0.02 -> 0.005`

It kept the loop052 observation layout, reward numbers, controller settings,
learning rate, update epochs, target KL, and network fixed.

The hypothesis failed:

- evaluator success dropped from loop052's `0.20` to `0.10`;
- mean gates dropped from loop052's `1.40` to `1.20`;
- crash rose from loop052's `0.80` to `0.90`;
- mean successful time worsened from `6.975s` to `7.13s`;
- W&B entropy fell, but gate/finish conversion did not improve enough to reach
  hard-eval progress.

Loop059 also matches the rollback criteria defined in its source packet:

- success `<=0.15`;
- mean gates `<1.40`;
- crash `>=0.85`;
- entropy lower but pass/finish conversion flat.

## Rejected Next Moves

Do not continue the same hypothesis.

Reason: low entropy did not produce meaningful gate progress and regressed
against loop052.

Do not mature loop059 to 60M.

Reason: its best checkpoint is below loop052 on success, crash, and mean gates.
The Level2 step-curve maturation rule is for promising branches; loop059 is not
promising relative to the current best.

Do not launch another automatic reward-number or PPO-number move immediately.

Reason: loop052-derived small repairs have repeatedly failed to convert W&B
proxies into hard-eval progress:

- loop053 nominal maturation;
- loop054 mild gate pressure;
- loop055 PPO update pressure;
- loop056 soft-centerline/light-plane;
- loop057 v8 observation screen;
- loop058 v8 maturation;
- loop059 low entropy.

## Required Next Work

Before the next training command, create a new source-backed research/decision
packet for a non-repeating named structural lane.

The packet must state:

- lane name;
- whether it starts from loop052 final;
- changed axis: observation, controller, reward structure, or training
  structure;
- why it does not repeat loops 053-059;
- train config and hard-eval config;
- unchanged `config/level3_dr.toml` target boundary;
- promotion and rollback criteria.

## Boundaries

- Do not modify `config/level3_dr.toml` track geometry or randomization.
- Do not edit `notebooks/train_level3_ppo.ipynb`.
- Do not continue v8.
- Do not continue the low-entropy lane.
- Do not launch another training chunk without attaching this decision packet
  and the loop059 analysis packet, or a newer approved structural packet.
