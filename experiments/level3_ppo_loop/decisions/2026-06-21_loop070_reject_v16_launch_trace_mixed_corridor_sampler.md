# Loop070 Decision: Reject V16 Maturation, Launch Trace-Mixed Corridor Sampler

Decision: launch_named_structural_lane

Pending gate resolved:

- trial_id: `level3_loop_070_structural_v16_hard_corridor_mature_loop069_25m_to_60m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_070_structural_v16_hard_corridor_mature_loop069_25m_to_60m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_070_structural_v16_hard_corridor_mature_loop069_25m_to_60m_analysis.json`

## Verdict

Reject same-hypothesis v16 continuation. Do not continue v16 to 90M.

Loop070 gave v16 a 60M-style maturation from the loop069 25M anchor. It failed
the rollback rule:

- best loop070 success: 0.05
- best loop070 mean gates: 1.05
- best loop070 crash rate: 0.95
- loop070 final: 0.10 success, 1.10 mean gates, 0.90 crash, 8.88s

The global best remains loop069 25M:

`lsy_drone_racing/control/checkpoints/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt`

Metrics:

- success rate: 0.20
- mean successful time: 6.675s
- crash rate: 0.80
- mean gates: 1.45

## Subagent Consensus

The three required reviewers agreed:

- evaluator metrics: reject same-hypothesis v16 maturation to 90M
- W&B/PPO diagnostics: PPO looked stable but behavior did not convert; prefer a
  named structural lane over reward-only or same-hypothesis continuation
- structure/research synthesis: v16 hard-corridor maturation is exhausted;
  launch a trace-conditioned mixed corridor sampler

## Next Lane

Launch named structural lane:

`v17_trace_conditioned_mixed_corridor_sampler_from_loop069_25m`

Contract:

- start from loop069 25M checkpoint
- train 30M screen with 5M checkpoint milestones
- keep training config `level3_dr.toml`
- keep hard eval `config/level3_dr.toml`
- keep v5 local-obstacle observation
- keep 2x256 MLP actor/critic
- keep loop052 nominal reward numbers
- keep constant learning rate 5e-5
- replace v16 `first_gate_hard_corridor` with training-only
  `track_generator_profile=trace_mixed_corridor`
- do not edit `config/level3_dr.toml`

The mixed profile keeps most episodes on the default Level3 generator while a
minority of episodes sample first-gate hard-corridor/yaw cases. This tests
whether trace-conditioned hard cases help without overfitting away from the
base Level3 distribution.

## Rollback Rule

Reject v17 unless it beats 0.20 success or clearly exceeds 1.45 mean gates with
crash rate no worse than 0.80. Do not assume the final checkpoint is best.
