# Loop068 Decision: Reject V15 Maturation, Hold For Targeted Seed Geometry Curriculum

## Decision

`hold_for_more_analysis`

Do not launch another train/evaluate chunk yet.

This packet resolves the post-run decision gate for:

- trial_id:
  `level3_loop_068_structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_068_structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_068_structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m_analysis.json`

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 target track geometry, gate layout, obstacle layout, or
  randomization.
- Do not accept any result unless it is hard-evaluated on unchanged
  `config/level3_dr.toml`.

## Evidence

Loop068 continued the v15 sensor15 curriculum from loop067's 10M checkpoint to
a 60M-level decision point.

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| loop052 final | 0.20 | 1.40 | 0.80 | 6.975s |
| loop067 10M | 0.20 | 1.60 | 0.80 | 7.445s |
| loop068 40M best | 0.20 | 1.25 | 0.80 | 6.620s |
| loop068 final | 0.00 | 0.70 | 1.00 | n/a |

Loop068 does not satisfy the loop067 promotion rule:

- success did not exceed `0.20`;
- mean gates regressed from loop067 10M `1.60` to loop068 best `1.25`;
- W&B pass, finish, and gate-plane-cross conversion remained flat;
- 45M and final degraded to zero success.

Global best remains:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

with:

- success rate: `0.20`
- mean gates: `1.40`
- crash rate: `0.80`
- mean successful time: `6.975s`

## Subagent Synthesis

Evaluator metrics:

- Reject continuing v15 to 90M.
- Loop068 improved successful time at one checkpoint but regressed mean gates
  and did not increase success.
- Later checkpoints eroded to zero success.

W&B/PPO diagnostics:

- PPO did not obviously explode, but there is no conversion signal.
- `train/total_reward` and `train/reward` trend down.
- `passed_gate_rate`, `finished_rate`, `gate_stage`, and
  `gate_plane_cross_rate` remain flat.
- Do not tune PPO hyperparameters silently from this result.

Structure/research synthesis:

- The immutable hard-eval boundary is intact.
- v15 sensor15 curriculum is now rejected as a continuation lane.
- Do not return to blind reward-only tuning.
- The remaining evidence still points to geometry-conditioned route learning.

## Blocked Training Actions

Do not launch:

- another v15/sensor15 continuation to 90M;
- loop032-style no-wrapper curriculum;
- unexplained reward-only tuning;
- hidden512 or GRU retry without a new source-backed lane packet;
- PPO hyperparameter changes without an explicit structural/training packet.

## Next Allowed Action

Create a named, runnable targeted seed/geometry sampler curriculum packet.

The next packet should define:

- lane name;
- sampler or curriculum mechanism;
- whether it starts from loop052 or another comparable hard-eval checkpoint;
- how it targets known hard early gate/obstacle corridors;
- exact training config and hard eval config;
- reward/controller/PPO numbers;
- W&B run naming;
- milestone hard-eval plan;
- rollback conditions versus loop052.

The next lane must keep:

- hard eval on unchanged `config/level3_dr.toml`;
- train robustness wrappers unless a packet explicitly proves they are the
  cause;
- v5 local-obstacle observation unless a new observation packet is approved.

Until that targeted seed/geometry sampler packet exists and the orchestrator
has a matching runnable structural hypothesis, the correct state is hold.
