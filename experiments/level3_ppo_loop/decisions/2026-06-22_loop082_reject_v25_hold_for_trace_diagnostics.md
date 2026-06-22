# Loop082 Decision: Reject V25, Hold For Trace Diagnostics

Decision: hold_for_more_analysis

Pending gate resolved:

- trial_id:
  `level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.json`

## Verdict

Reject v25. Do not promote it and do not mature it.

Do not launch another train/evaluate chunk until a trace/seed-retention
diagnostic compares loop078, v24, and v25 on the same hard-eval seed set.

## Evidence

Loop082/v25 failed its rollback gate:

- loop078 global best: 0.25 success, 2.05 mean gates, 0.75 crash, 8.048s
- loop081/v24 best: 0.15 success, 1.45 mean gates, 0.85 crash, 7.173s
- loop082/v25 best: 0.10 success, 1.35 mean gates, 0.90 crash, 7.25s

V25 is worse than both loop078 and v24 on success, crash rate, and mean gates.
Every v25 milestone stayed at 0.10 success and 0.90 crash, with mean gates only
1.35-1.40.

## Reviewer Consensus

Evaluator metrics:

- Reject v25.
- It is not promising enough for step-curve maturation.
- The faster-than-loop078 successful subset is not useful because success and
  gate progress regressed.

W&B/PPO diagnostics:

- PPO looks stable enough: low KL, low clip fraction, stable explained
  variance, and no entropy collapse.
- Training reward improved, but W&B race signals and hard eval did not convert.
- Do not silently change PPO numbers or mature the same v25 hypothesis.

Structure/research synthesis:

- Reject v25.
- V24 and v25 both degraded retention after aperture features were appended.
- Before v26, run a trace/seed-retention diagnostic comparing loop078, v24, and
  v25 endpoint classes and successful seeds.

## Required Diagnostic

Run a non-training diagnostic on unchanged `config/level3_dr.toml`:

- loop078 final global best
- loop081/v24 final
- loop082/v25 best checkpoint, currently 5M

The diagnostic must record successful seeds, lost successful seeds, mean gates,
gate transition endpoints, and near-gate obstacle/frame failure patterns. It
should produce a markdown synthesis before any next structural lane or reward
change.

## Boundary

Do not modify the Level3 track geometry, randomization, gates, or obstacles.
Do not launch another training chunk until the trace diagnostic is reviewed.
