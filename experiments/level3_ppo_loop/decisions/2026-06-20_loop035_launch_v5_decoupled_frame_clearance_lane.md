# Main-Agent Decision After loop035

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Named next lane:

`v5_decoupled_frame_clearance_low_pressure_reward`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not continue loop035 unchanged.
- Do not promote loop035 as a parent checkpoint.
- Use loop020 25M as the parent checkpoint/global-best anchor.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m_analysis.md`
- Synthesis:
  `experiments/level3_ppo_loop/research/2026-06-20_loop035_decoupled_frame_clearance_synthesis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m`

Best loop035 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m/level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m_step_005000000.ckpt`
- Success rate: `0.00`
- Mean successful time: `null`
- Crash rate: `1.00`
- Mean gates: `0.85`

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

## Reviewer Synthesis

Evaluator metrics:

- Reject loop035.
- Do not mature it toward 60M-90M.
- All evaluated loop035 checkpoints had `0.00` success and `1.00` crash.
- Mean gates degraded after 5M: `0.85 -> 0.20 -> 0.10 -> 0.10`.

W&B/PPO diagnostics:

- Gate/finish conversion failed:
  - `race/passed_gate_rate` tail mean about `0.000122`;
  - `race/finished_rate` stayed `0.0`.
- PPO movement did not look useful:
  - KL near zero;
  - clip fraction `0.0`;
  - entropy high/rising;
  - value loss very large.
- The frame-clearance signal existed, but did not convert:
  - `reward_components/missed_gate` tail mean about `-50.78`;
  - `reward_components/gate_plane` tail mean about `0.0005`;
  - `race/wrong_side_gate_rate` rose.

Structure/research synthesis:

- loop035 points to reward-structure failure.
- `legacy_frame_clearance` coupled dense near-plane frame pressure to the same
  `missed_gate_penalty` used for discrete missed-gate events.
- Lowering `missed_gate_penalty` alone is not clean because it weakens the
  discrete event and dense pressure together.
- The next mechanism should decouple those channels.

## Next Lane

Name:

`v5_decoupled_frame_clearance_low_pressure_reward`

Proposal:

`structural_v5_decoupled_frame_clearance_low_pressure_reward_20m`

Training setup:

- Start from the loop020 global-best checkpoint selected from `state.json`.
- Train config: `level3_dr.toml`.
- Hard eval config: `level3_dr.toml`.
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Train for `20_000_000` steps with `5_000_000` checkpoint interval.
- Use W&B project `ADR-PPO-Racing-Level3`.

Reward-structure change:

- `reward_structure=decoupled_frame_clearance`

Changed numeric values:

- `gate_plane_bonus=18.0`
- `missed_gate_penalty=8.0`
- `gate_frame_pressure_coef=1.5`
- `obstacle_coef=4.5`
- `obstacle_margin=0.3`

Keep fixed from loop020:

- v5 observation layout;
- full `90deg` roll/pitch action authority;
- no action low-pass;
- PPO settings;
- completion-backloaded gate pass/back/finish rewards.

## Rejected Next Moves

Rejected:

- continue loop035 unchanged;
- mature loop035 to 60M-90M;
- repeat `legacy_frame_clearance`;
- tune only `missed_gate_penalty` while event miss and dense frame pressure are
  coupled;
- modify Level3 track geometry or randomization.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_decoupled_frame_clearance_low_pressure_reward \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop035_decoupled_frame_clearance_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop035_launch_v5_decoupled_frame_clearance_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
