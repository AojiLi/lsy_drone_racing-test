# Loop080 Decision: Reject V23, Launch V24 Hybrid Aperture-Corridor Observation

Decision: launch_named_structural_lane

Pending gate resolved:

- trial_id: `level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m_analysis.json`

## Verdict

Reject v23. Do not promote it and do not mature it.

Launch:

`v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m`

## Evidence

Loop080/v23 failed its rollback gate against loop078:

- loop078 global best: 0.25 success, 2.05 mean gates, 0.75 crash, 8.048s
- loop080 best evaluator milestone: 0.20 success, 2.00 mean gates, 0.80 crash,
  8.855s
- loop080 final: 0.10 success, 1.45 mean gates, 0.90 crash, 6.77s

The final checkpoint's speed is not useful because it appears only on a sparse
10% success subset. The hard-eval target remains success first.

## Reviewer Consensus

Evaluator metrics:

- Reject v23.
- The 10M checkpoint is the best-looking milestone but is still below loop078
  on success, crash, mean gates, and successful time.

W&B/PPO diagnostics:

- PPO was stable enough: low/flat KL, near-zero clip fraction, steady entropy,
  improving explained variance.
- W&B race metrics did not convert into hard-eval progress.
- Do not silently change PPO optimizer/training numbers.

Structure/research synthesis:

- Reject v23.
- The active frame-clearance reward did not solve the observed gate/frame and
  near-obstacle failures.
- Next useful test should be observation structure, not another reward scalar:
  preserve v8 gate-corridor obstacle features and append v9-style aperture
  margin/frame-clearance geometry.

## Next Structural Lane

Contract:

- start from loop078 final
- train on `level3_dr.toml`
- hard eval on unchanged `config/level3_dr.toml`
- keep 2x256 Tanh MLP actor/critic
- keep loop078/v22 reward numbers and PPO/controller settings
- use a new hybrid observation layout:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`
- the layout is v8 gate-corridor obstacle features plus v9 aperture-margin
  features appended at the end
- warm-start from loop078 by zero-padding only the new appended input weights
- run one 20M screen with 5M checkpoint evaluation
- log to W&B project `ADR-PPO-Racing-Level3`

## Rationale

v23 changed reward structure and safety pressure but kept the same v8
observation, and it lost retention. Existing v9 aperture-margin support was
previously tested from the older loop052 family, not from the stronger
loop078/v8 frontier. V24 isolates whether the controller needs explicit
aperture/frame geometry in the observation while keeping reward and PPO numbers
fixed.

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
  --structural-hypothesis v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop080_reject_v23_launch_v24_hybrid_aperture_corridor_obs.md
```
