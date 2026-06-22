# Main-Agent Decision After loop034 Synthesis

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Named next lane:

`v5_frame_clearance_pass_conversion_reward`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not continue loop034 unchanged.
- Do not tune another low-pass alpha.
- Use loop020 25M as the parent checkpoint.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m_analysis.md`
- Hold decision:
  `experiments/level3_ppo_loop/decisions/2026-06-20_hold_after_loop034_pass_conversion_synthesis.md`
- Synthesis:
  `experiments/level3_ppo_loop/research/2026-06-20_loop034_frame_clearance_pass_conversion_synthesis.md`

The latest synthesis concludes:

- loop027 reward rebalance failed;
- loop033 PPO-pressure/entropy failed;
- loop034 mild low-pass failed;
- loop020 remains the global best;
- failures are concentrated around early gate frames and nearby obstacles;
- the next mechanism should directly target centered gate-plane crossing and
  pre-collision frame clearance.

## Next Lane

Name:

`v5_frame_clearance_pass_conversion_reward`

Proposal:

`structural_v5_frame_clearance_pass_conversion_reward_20m`

Training setup:

- Start from the loop020 global-best checkpoint selected from `state.json`.
- Train config: `level3_dr.toml`.
- Hard eval config: `level3_dr.toml`.
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Train for `20_000_000` steps with `5_000_000` checkpoint interval.
- Use W&B project `ADR-PPO-Racing-Level3`.

Reward-structure change:

- `reward_structure=legacy_frame_clearance`

`legacy_frame_clearance` keeps loop020's legacy staged reward family, but adds:

- centered current-gate plane crossing reward through `gate_plane_bonus`;
- continuous near-plane frame-clearance penalty through `missed_gate_penalty`.

Changed numeric values:

- `gate_plane_bonus=35.0`
- `missed_gate_penalty=18.0`
- `obstacle_coef=6.0`
- `obstacle_margin=0.35`

Keep fixed from loop020:

- v5 observation layout;
- full `90deg` roll/pitch action authority;
- no action low-pass;
- PPO settings;
- completion-backloaded gate pass/back/finish rewards.

## Rationale

loop020 is still the only branch with meaningful local pass conversion.
However, 40-seed crash taxonomy shows early crashes around gate frames and
obstacles. Smoother controller variants reduced command saturation but lost
gate progress. This lane keeps loop020's useful action authority and pass
reward while adding training pressure for centered gate-plane crossing before
the hard collision event.

## Promotion And Rollback

Promote or mature only if a hard-eval checkpoint shows at least one:

- success rate above loop020: `>0.15`;
- mean gates above loop020: `>1.45`;
- same success as loop020 with materially lower crash or command saturation.

Reject if:

- best success remains `<=0.05`;
- mean gates stay below `1.10`;
- crash remains `>=0.95`;
- W&B `gate_plane`/`missed_gate` terms move but hard-eval pass/finish
  conversion stays flat;
- the policy avoids the gate corridor instead of crossing it.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_frame_clearance_pass_conversion_reward \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop034_frame_clearance_pass_conversion_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop034_launch_v5_frame_clearance_pass_conversion_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
