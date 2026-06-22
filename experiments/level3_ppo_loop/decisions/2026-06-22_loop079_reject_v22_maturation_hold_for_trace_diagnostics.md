# Loop079 Decision: Reject V22 Maturation, Hold For Trace Diagnostics

Decision: hold_for_more_analysis

Pending gate resolved:

- trial_id: `level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m_analysis.json`

## Verdict

Reject loop079 for promotion and do not continue v22 unchanged to 90M yet.

Loop079 failed the rollback thresholds defined in the loop078 maturation
decision:

- success fell below `0.20`
- mean gates fell below `2.00`
- crash rose above `0.80`

Do not change PPO/training numbers from this evidence. Do not apply the
analyzer's repeated gate-reward increase automatically. The failure is a
hard-eval conversion regression, not a clear PPO optimization collapse.

## Hard-Eval Evidence

Best loop079 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m/level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m_step_030000000.ckpt`

Hard eval on unchanged `config/level3_dr.toml`:

- success rate: 0.15
- mean successful time: 7.0067s
- crash rate: 0.85
- timeout rate: 0.00
- mean gates: 1.55
- target met: false

Loop079 milestones:

- 20M: 0.10 success, 0.90 crash, 1.55 mean gates, 8.30s
- 25M: 0.05 success, 0.95 crash, 1.05 mean gates, 6.86s
- 30M: 0.15 success, 0.85 crash, 1.55 mean gates, 7.0067s
- 35M: 0.10 success, 0.90 crash, 1.15 mean gates, 8.91s
- final: 0.15 success, 0.85 crash, 1.35 mean gates, 7.9933s

Global best remains loop078 final:

`lsy_drone_racing/control/checkpoints/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m/level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_final.ckpt`

- success rate: 0.25
- mean successful time: 8.048s
- crash rate: 0.75
- mean gates: 2.05

## Reviewer Consensus

Evaluator metrics:

- Hold.
- Reject loop079 for promotion or further same-lane maturation.
- Loop079 improved successful time only, while losing success, gates, and
  crash rate against loop078.

W&B/PPO diagnostics:

- PPO optimization looked stable: low KL, low clip fraction, healthy explained
  variance, and no obvious divergence.
- Train reward improved but did not convert to hard-eval success or gate
  progress.
- Do not treat this as a learning-rate, entropy, minibatch, epoch, hidden-size,
  or target-KL problem without a named training-structure lane.

Structure/research synthesis:

- Hold for diagnostics.
- The branch diagnosis is `hold_plateau_no_conversion`.
- Do not continue v22 unchanged and do not change reward/training numbers until
  the seed-level regression is understood.

## Required Diagnostic Before Next Training

Run a v22-specific diagnostic comparing:

- loop078 final
- loop079 20M
- loop079 25M
- loop079 30M
- loop079 35M
- loop079 final

Use fixed hard-eval seeds on unchanged `config/level3_dr.toml`.

Focus:

- success seed retention and loss
- gate0-to-gate1 and gate1-to-gate2 transition quality
- crash localization by gate/obstacle/frame region
- obstacle clearance and gate-corridor alignment
- tilt and command saturation
- speed-vs-crash tradeoff

No next training command is approved until this diagnostic is written and a new
main-agent decision packet chooses either a named structural lane or a bounded
reward/training-number hypothesis.
