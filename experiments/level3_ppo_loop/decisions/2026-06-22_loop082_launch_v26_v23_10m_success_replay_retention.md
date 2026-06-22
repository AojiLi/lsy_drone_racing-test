# Loop082 Decision: Launch V26 V23-10M Success Replay Retention

Decision: launch_named_structural_lane

Prior hold resolved:

- trial_id:
  `level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.json`
- hold decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop082_reject_v25_hold_for_trace_diagnostics.md`

## Verdict

Launch:

`v26_v23_10m_success_replay_retention_20m`

## Why V26 Is Different

Do not continue v25. Do not run another aperture observation lane. Do not use
naive weight interpolation.

The post-hold diagnostics show:

- loop078 successful seeds: 4, 9, 12, 18, 19
- v23 10M successful seeds: 4, 5, 12, 18
- v24 successful seeds: 4, 8, 9
- v25 successful seeds: 8, 9

V23 10M is the closest non-best variant because it preserves 4/12/18 and adds
seed 5, although it loses 9/19. V26 uses v23 10M as the anchor and trains with
low-probability replay over the union success set:

`[4, 5, 9, 12, 18, 19]`

The hypothesis is explicit seed-retention repair, not blind maturation.

## Next Structural Lane

Contract:

- start from v23 10M
- train on `level3_dr.toml`
- hard eval on unchanged `config/level3_dr.toml`
- keep v8 gate-corridor obstacle observation
- keep 2x256 Tanh MLP actor/critic
- keep v23 decoupled frame-clearance reward settings
- use training-only profile `loop078_v23_success_replay_lowprob`
- run one 20M screen with 5M checkpoint evaluation
- log to W&B project `ADR-PPO-Racing-Level3`

## Boundary

This does not modify Level3 track geometry, randomization, gates, or obstacles
in `config/level3_dr.toml`. The replay profile is a named training-only sampler
inside the PPO training command. Final acceptance remains hard eval on
unchanged `config/level3_dr.toml`.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v26_v23_10m_success_replay_retention_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_v26_v23_10m_success_replay_retention_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop082_launch_v26_v23_10m_success_replay_retention.md
```
