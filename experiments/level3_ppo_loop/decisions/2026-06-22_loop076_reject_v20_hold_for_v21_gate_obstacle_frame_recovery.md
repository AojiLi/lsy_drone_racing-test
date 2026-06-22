# Loop076 Decision: Reject V20, Hold For V21 Gate/Obstacle/Frame Recovery

Decision: hold_for_more_analysis

Pending gate resolved:

- trial_id: `level3_loop_076_structural_v20_loop071_default_distribution_recovery_20m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_076_structural_v20_loop071_default_distribution_recovery_20m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_076_structural_v20_loop071_default_distribution_recovery_20m_analysis.json`

## Verdict

Reject v20 default-distribution recovery. Do not continue v20 to 60M. Do not
promote any loop076 checkpoint.

Best loop076 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_076_structural_v20_loop071_default_distribution_recovery_20m/level3_loop_076_structural_v20_loop071_default_distribution_recovery_20m_step_005000000.ckpt`

Metrics on hard eval `config/level3_dr.toml`:

- success rate: 0.20
- mean successful time: 7.935s
- crash rate: 0.80
- timeout rate: 0.00
- mean gates: 1.65
- target met: false

The global best remains loop069 25M:

`lsy_drone_racing/control/checkpoints/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt`

- success rate: 0.20
- mean successful time: 6.675s
- crash rate: 0.80
- mean gates: 1.45

## Milestone Evidence

| Checkpoint | Success | Mean Gates | Crash | Mean Success Time |
| --- | ---: | ---: | ---: | ---: |
| loop076 5M | 0.20 | 1.65 | 0.80 | 7.935s |
| loop076 10M | 0.05 | 1.15 | 0.95 | 8.380s |
| loop076 15M | 0.05 | 1.35 | 0.95 | 7.820s |
| loop076 final | 0.15 | 1.70 | 0.85 | 7.267s |

The 5M checkpoint is the correct loop076 milestone by success/crash. The final
checkpoint has slightly higher mean gates but lower success and higher crash,
so it is not a promotion checkpoint.

Comparison:

- loop076 ties loop069 on success and crash, improves mean gates from 1.45 to
  1.65, but is much slower: 7.935s versus 6.675s.
- loop076 fails loop071's diagnostic frontier: loop071 20M had 0.25 success,
  2.00 mean gates, and 0.75 crash.

## Three-Reviewer Consensus

Evaluator metrics:

- Hold/reject on evaluator evidence.
- Do not mature loop076.
- Keep loop069 25M as global best.

W&B/PPO diagnostics:

- PPO is not the primary failure: KL, clip fraction, entropy, value loss,
  explained variance, and SPS are controlled.
- Training reward improved, but race proxies and hard eval did not convert.
- Do not change PPO/training numbers from this evidence alone.

Structure/research synthesis:

- Reject v20 continuation.
- Do not return to seed replay.
- Next useful lane should target the persistent default-distribution failure:
  gate acquisition with obstacle/frame collisions.

## Next Action

No next training command is approved by this packet.

Prepare a new named structural lane before training resumes:

`v21_default_gate_obstacle_frame_recovery_from_loop071_20m`

Initial design constraints:

- keep hard eval on unchanged `config/level3_dr.toml`
- train on `level3_dr.toml` unless a clearly labeled training-only curriculum
  packet is written
- start from loop071 20M unless a trace/evaluator packet proves loop076 5M has
  better transferable per-seed behavior
- keep PPO/training numbers fixed initially
- target gate acquisition plus obstacle/frame collision failure
- avoid seed replay as the next intervention
- write a new decision/research packet and dry-run the lane before launch
