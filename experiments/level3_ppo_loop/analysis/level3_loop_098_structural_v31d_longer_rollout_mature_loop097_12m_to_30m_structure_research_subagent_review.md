# Structure/Research Synthesis Review: loop098

Verdict: do not continue v31d clean-PPO maturation as-is.

loop098 failed the loop097 promotion gate:

- loop098 best: `19/100` success, `1.63` mean gates, `81%` crash, `7.496s`.
- loop097 best: `20/100` success, `1.66` mean gates, `80%` crash, `7.055s`.
- Across milestones, no checkpoint cleanly expanded the frontier. The run added
  eight success seeds but lost nine.

Recommended decision: `launch_named_structural_lane`, not reward/training-number
tuning. PPO diagnostics look stable rather than broken, while gate/finish
conversion stayed flat. Reward numbers should stay behind framework-level
value/critic/training-structure work.

Exact next family: `v32_asymmetric_privileged_critic_support_parity`, followed
only after parity by a bounded screen such as
`v32_asymmetric_privileged_critic_clean_ppo_5m`.

Conditions:

- Keep `config/level3.toml` unchanged for hard eval.
- Keep the deployed path as
  `v5 observation/history -> PPO actor -> roll/pitch/yaw/thrust`.
- Privileged/full-state input is critic-only during training.
- First implement trainer/evaluator/checkpoint metadata support.
- Then pass zero-update actor parity against the loop097/v31d 12M best
  checkpoint on validation seeds 101-200.
- Only after parity passes, run a 5M milestone screen with hard eval on
  unchanged `config/level3.toml`.
