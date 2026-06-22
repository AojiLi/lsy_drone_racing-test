# Loop081 Decision: Reject V24, Launch V25 Minimal Aperture Ablation

Decision: launch_named_structural_lane

Pending gate resolved:

- trial_id:
  `level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m_analysis.json`

## Verdict

Reject v24. Do not promote it and do not mature it.

Launch:

`v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m`

## Evidence

Loop081/v24 failed its rollback gate against loop078:

- loop078 global best: 0.25 success, 2.05 mean gates, 0.75 crash, 8.048s
- loop081/v24 best final: 0.15 success, 1.45 mean gates, 0.85 crash, 7.173s
- loop081 milestones:
  - 5M: 0.15 success, 1.25 mean gates, 0.85 crash
  - 10M: 0.10 success, 1.25 mean gates, 0.90 crash
  - 15M: 0.10 success, 1.50 mean gates, 0.90 crash
  - final: 0.15 success, 1.45 mean gates, 0.85 crash

The faster successful-time subset is not useful because success and gate
progress regressed. The hard-eval target remains success first.

## Reviewer Consensus

Evaluator metrics:

- Reject v24.
- No checkpoint preserved loop078 retention.
- The best v24 checkpoint still misses success, crash, gates, and target time.

W&B/PPO diagnostics:

- PPO was stable enough: low KL, low clip fraction, stable entropy, acceptable
  explained variance.
- Training reward improved, but gate pass and finish rates did not convert.
- Do not silently change PPO optimizer/training numbers.

Structure/research synthesis:

- Reject v24 as implemented.
- Next move should be a smaller observation ablation, not v24 maturation.
- Keep Level3 unchanged and start from loop078 final.

## Next Structural Lane

Contract:

- start from loop078 final
- train on `level3_dr.toml`
- hard eval on unchanged `config/level3_dr.toml`
- keep 2x256 Tanh MLP actor/critic
- keep loop078/v22 reward numbers and PPO/controller settings
- use a new minimal aperture observation layout:
  `level3_gate_corridor_aperture_margin_minimal_2obs_local_history_v11`
- the layout is v8 gate-corridor obstacle features plus only five aperture
  margin features, not the full duplicated v9 block
- warm-start from loop078 by zero-padding only the new appended input weights
- run one 20M screen with 5M checkpoint evaluation
- log to W&B project `ADR-PPO-Racing-Level3`

## Rationale

V24 appended the full aperture-margin block to v8. But v8 already contains
`target_progress` and current gate-frame position through the phase-progress
block, so v10 duplicates part of the signal and may disturb the loop078
frontier. V25 tests only the missing clearance information: square-aperture and
radial margins.

## Promotion And Rollback

Promote or mature if a milestone reaches one of:

- success `> 0.25`
- success `>= 0.25` and mean gates `>= 2.05`
- success `>= 0.25` and crash `< 0.75`
- success `>= 0.25`, mean gates `>= 2.05`, and mean successful time moves
  closer to `<= 7.0s`

Reject or hold if it falls below loop078 retention:

- success `< 0.25`
- mean gates `< 2.05`
- crash `> 0.75`

Do not modify the Level3 track geometry, randomization, gates, or obstacles.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/diagnostics/2026-06-22_loop081_v25_minimal_aperture_ablation_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop081_reject_v24_launch_v25_minimal_aperture_ablation_obs.md
```
