# Loop080 V24 Hybrid Aperture-Corridor Observation Synthesis

Scope: source-backed local synthesis after rejecting loop080/v23. This does not
modify `config/level3_dr.toml`. Hard acceptance remains success rate `>= 0.60`
and mean successful time `<= 7.0s` on unchanged `config/level3_dr.toml`.

Inputs:

- Loop080 analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m_analysis.md`
- Loop080 decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop080_reject_v23_launch_v24_hybrid_aperture_corridor_obs.md`
- Existing v8 observation lane:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- Existing v9 aperture-margin machinery:
  `level3_gate_aperture_margin_2obs_local_history_v9`

## Summary

Loop080/v23 is rejected. Activating frame-clearance reward and increasing
obstacle pressure did not improve hard-eval success or gate progress. The best
loop080 milestone stayed below loop078, and final regressed to 0.10 success.

The next test should isolate observation structure rather than another reward
scalar:

- preserve loop078/v8 gate-corridor obstacle behavior;
- append v9-style explicit aperture-margin geometry;
- warm-start from loop078 by zero-padding only the newly appended input weights;
- keep reward, PPO, controller, and target track fixed.

## Hypothesis

`v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m`

The policy may need explicit square-aperture clearance and radial margin
features in addition to the v8 gate-corridor obstacle frame. This tests whether
more directly observable frame geometry improves gate/frame collision handling
without changing reward structure.

## Contract

- initial checkpoint: loop078 final
- train config: `level3_dr.toml`
- hard eval config: unchanged `level3_dr.toml`
- observation layout:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`
- policy: 2x256 Tanh MLP
- reward structure: `legacy_staged`
- reward/PPO/controller numbers: loop078/v22 defaults
- training horizon: 20M with 5M checkpoint evaluation

## Rollback

Reject or hold if the lane fails to preserve loop078 retention:

- success below 0.25
- mean gates below 2.05
- crash above 0.75

Promote only if it creates a hard-eval frontier on unchanged `config/level3_dr.toml`.
