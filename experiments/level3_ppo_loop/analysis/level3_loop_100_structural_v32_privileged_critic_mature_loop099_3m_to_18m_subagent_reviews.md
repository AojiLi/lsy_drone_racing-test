# loop100 Subagent Reviews

Trial:
`level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m`

## evaluator_metrics

- Recommendation: `launch_named_structural_lane`.
- Best loop100 checkpoint by success was final:
  `lsy_drone_racing/control/checkpoints/level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m/level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m_final.ckpt`.
- Metrics: 19% success, 7.304s mean successful time, 81% crash, 1.65 mean
  gates on unchanged `config/level3.toml`.
- It did not beat loop097 global best: 20% success, 7.055s, 80% crash,
  1.66 mean gates.
- Intermediate 3M and 14M checkpoints had higher mean gates, but not enough
  success/crash conversion to continue v32.

## wandb_ppo_diagnostics

- Recommendation: `launch_named_structural_lane`.
- PPO did not collapse, but the training signal did not convert into hard-eval
  progress.
- `train/reward` improved from about -126 to -55, while passed-gate,
  finished, and crashed rates were flat or slightly worse.
- PPO updates were weak but stable: `approx_kl=0.000412`, `clipfrac=0.0`,
  policy loss near zero, entropy flat, explained variance about 0.774.
- Conclusion: do not continue privileged-Critic maturation, reward-number
  tuning, or W&B-reward-led training. Move to a training-distribution lane.

## structure_research_synthesis

- Recommendation: `launch_named_structural_lane`.
- Suggested lane: `v33_gate_phase_reset_curriculum`.
- The v32 stop condition was not met: no success above 20%, no stable mean-gate
  expansion beyond 1.66, and crash stayed around 81%.
- Diagnosis: current bottleneck is more likely training distribution and gate
  acquisition practice than value signal alone.
- Boundary: do not edit Level3 track geometry or randomization for acceptance;
  keep hard eval fixed on unchanged `config/level3.toml`.
