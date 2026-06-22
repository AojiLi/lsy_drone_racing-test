# Loop068 Decision: Launch First-Gate Hard-Corridor Sampler

Decision: launch_named_structural_lane

Pending gate resolved:

- trial_id: `level3_loop_068_structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_068_structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_068_structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m_analysis.json`

## Verdict

Reject continuing v15/sensor15 maturation. Loop068 did not improve over the
global loop052 best: best checkpoint stayed at 0.20 success, mean gates fell to
1.25, and the final checkpoint collapsed to 0.00 success with 1.00 crash rate.
Do not continue this lane to 90M.

## Next Lane

Launch named structural lane
`v16_first_gate_hard_corridor_sampler_from_loop052`.

Contract:

- hard eval remains `config/level3_dr.toml`
- do not edit `config/level3_dr.toml`
- start from loop052 final checkpoint
- keep v5 local-obstacle observation
- keep 2x256 MLP actor/critic
- keep loop052 nominal reward numbers
- keep constant learning rate 5e-5
- train for 30M with 5M checkpoint milestones
- use training-only `track_generator_profile=first_gate_hard_corridor`

The profile samples a tighter first-obstacle corridor and wider first-gate yaw
range during training. This is a targeted curriculum for the observed
first-gate/first-obstacle failure mode; acceptance still requires hard eval on
the unchanged Level3 track distribution.

## Promotion Rule

Promote to 60M only if the 30M screen shows at least one of:

- success rate above loop052's 0.20
- mean gates meaningfully above 1.40 with crash rate no worse than 0.80
- 0.20 success with faster mean successful time and improved gate conversion

Otherwise reject the lane and move to the next explicit structure/reward
hypothesis instead of blind continuation.
