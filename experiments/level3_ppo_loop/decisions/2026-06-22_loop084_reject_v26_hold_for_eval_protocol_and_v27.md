# Loop084 Decision: Reject V26, Hold For Evaluation Protocol And V27

Decision: hold_for_more_analysis

Pending gate resolved:

- trial_id:
  `level3_loop_084_structural_v26_v23_10m_success_replay_retention_mature_to_60m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_084_structural_v26_v23_10m_success_replay_retention_mature_to_60m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_084_structural_v26_v23_10m_success_replay_retention_mature_to_60m_analysis.json`

## Verdict

Reject v26 success-replay retention.

Do not launch loop085 or any additional long training run until the evaluator
uses separated seed splits and the historical frontier checkpoints have been
re-evaluated on unseen validation seeds.

Global best remains:

`lsy_drone_racing/control/checkpoints/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_final.ckpt`

## Evidence

Loop084 best checkpoint was the 30M checkpoint:

- success: 0.10
- mean gates: 1.25
- crash: 0.90
- mean successful time: 6.30s

This is worse than both relevant anchors:

- loop078 final: 0.25 success, 2.05 mean gates, 0.75 crash, 8.048s
- loop083 15M: 0.20 success, 2.00 mean gates, 0.80 crash, 7.595s

The faster success time in loop084 is not useful because it is conditioned on
only two successful episodes out of twenty. Reliability regressed.

## Stop Rules

Triggered:

- v26 maturation failed to exceed loop078 on hard eval.
- loop084 did not preserve loop083's 15M success behavior.
- continued training produced non-monotonic forgetting, not a useful step curve.

Hold before any new training.

## Immediate Work

1. Add evaluator support for fixed seed manifests.
2. Add Wilson confidence intervals and failure taxonomy to evaluator outputs.
3. Split seeds into `dev_seen`, `validation_unseen`, and `final_locked`.
4. Re-evaluate historical frontier checkpoints on `validation_unseen`.
5. Choose the true anchor by validation success, lower confidence bound, crash,
   mean gates, then successful time.
6. Only then launch a new named v27 experiment.

## Forbidden Until Re-Evaluation

- continuing v26
- continuing to 90M
- aperture observation variants
- hidden512
- GRU
- weight interpolation
- exact hard-eval seed replay
- from-scratch baselines
- PPO optimizer changes
- `num_envs` changes

The next experimental direction should be a teacher-anchored failure-correction
lane that addresses successful-behavior forgetting without modifying
`config/level3_dr.toml`.

