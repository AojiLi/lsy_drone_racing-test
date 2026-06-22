# Loop069 Decision: Continue First-Gate Hard-Corridor Sampler To 60M

Decision: continue_same_hypothesis

Pending gate resolved:

- trial_id: `level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_analysis.json`

## Evidence

Loop069 best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt`

Hard eval on unchanged `config/level3_dr.toml`:

- success rate: 0.20
- mean successful time: 6.675s
- crash rate: 0.80
- mean gates: 1.45
- target met: false

Comparison:

- vs loop052: same success and crash, faster mean successful time, mean gates
  improved from 1.40 to 1.45
- vs loop068: same success and crash, mean gates improved from 1.25 to 1.45
- loop069 final regressed to 0.10 success and 1.10 mean gates, so do not use
  final as the continuation anchor

## Subagent Consensus

The three required reviewers agreed:

- evaluator metrics: promote narrowly to a 60M maturation run
- W&B/PPO diagnostics: optimizer is stable; continue from 25M, not final
- structure/research synthesis: choose `continue_same_hypothesis`; do not take
  the analyzer's generic reward bump before maturing the promising sampler

## Next Run Contract

Launch named continuation lane
`v16_first_gate_hard_corridor_sampler_maturation_from_loop069_25m`.

Contract:

- start from loop069 25M checkpoint
- train 35M additional steps to reach a 60M-level horizon
- checkpoint every 5M
- keep training config `level3_dr.toml`
- keep hard eval `config/level3_dr.toml`
- keep v5 local-obstacle observation
- keep 2x256 MLP actor/critic
- keep loop052 nominal reward numbers
- keep constant learning rate 5e-5
- keep training-only `track_generator_profile=first_gate_hard_corridor`
- do not edit `config/level3_dr.toml`

## Rollback Rule

Reject or change lane after this maturation if milestones do not beat 0.20
success or clearly lift mean gates above 1.45 without crash worsening. Do not
assume the final checkpoint is best.
