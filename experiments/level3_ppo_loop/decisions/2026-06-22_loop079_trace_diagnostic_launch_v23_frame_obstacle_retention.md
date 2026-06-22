# Loop079 Decision: Launch V23 Frame/Obstacle Retention Lane

Decision: launch_named_structural_lane

Prior hold gate:

- trial_id: `level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m_analysis.md`
- diagnostic_synthesis: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop079_v22_maturation_regression_synthesis.md`

## Verdict

Launch a new named lane instead of continuing v22 unchanged.

`v23_v22_frame_obstacle_retention_from_loop078_final_20m`

## Evidence

Loop079 same-hypothesis maturation regressed from the loop078 global best:

- loop078 final: 0.25 success, 2.05 mean gates, 0.75 crash, 8.048s
- loop079 best: 0.15 success, 1.55 mean gates, 0.85 crash, 7.0067s

The v22 trace diagnostic shows success-retention loss:

- loop078 successful seeds: `[4, 9, 12, 18, 19]`
- loop079 30M successful seeds: `[4, 9, 16]`
- loop079 final successful seeds: `[1, 4, 9]`

Weight interpolation between loop078 and loop079 did not recover the union. The
best interpolation reached only 0.20 success and 2.00 mean gates, below loop078.

## Next Structural Lane

Contract:

- start from loop078 final
- train on `level3_dr.toml`
- hard eval on unchanged `config/level3_dr.toml`
- keep v8 gate-corridor obstacle observation
- keep 2x256 Tanh MLP actor/critic
- keep controller action limits and lowpass settings
- run one 20M screen with 5M checkpoint evaluation
- log to W&B project `ADR-PPO-Racing-Level3`

Changed training/reward-structure numbers:

- `learning_rate`: `5e-5` -> `2e-5`
- `reward_structure`: `legacy_staged` -> `decoupled_frame_clearance`
- `gate_frame_pressure_coef`: `0.0` -> `1.0`
- `obstacle_coef`: `8.0` -> `10.0`
- `obstacle_margin`: `0.4` -> `0.45`
- `time_penalty`: `0.03` -> `0.015`

Everything else stays aligned with loop078/v22.

## Rationale

This lane targets the two observed failure modes without changing the target
track:

- lower LR tests whether loop078 skills can be retained while adapting;
- `decoupled_frame_clearance` makes frame pressure active, unlike
  `legacy_staged`;
- slightly stronger obstacle safety targets near-gate obstacle crashes;
- lower time pressure avoids optimizing speed at the expense of success.

## Promotion And Rollback

Promote or mature if a milestone reaches one of:

- success `> 0.25`
- success `>= 0.25` and crash `< 0.75`
- success `>= 0.25`, mean gates `>= 2.05`, and mean successful time moves
  closer to `<= 7.0s`

Reject or hold if it falls below:

- success `< 0.20`
- mean gates `< 2.00`
- crash `> 0.80`

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v23_v22_frame_obstacle_retention_from_loop078_final_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m_analysis.md \
  --research-packet experiments/level3_ppo_loop/diagnostics/2026-06-22_loop079_v22_maturation_regression_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop079_trace_diagnostic_launch_v23_frame_obstacle_retention.md
```
