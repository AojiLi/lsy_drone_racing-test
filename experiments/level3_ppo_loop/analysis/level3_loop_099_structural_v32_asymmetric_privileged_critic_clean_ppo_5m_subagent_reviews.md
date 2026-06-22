# Level3 Loop099 Subagent Reviews

Trial: `level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_analysis.md`

Final target remains hard eval on unchanged `config/level3.toml`: success rate
`>= 0.60` and mean successful time `<= 7.0s`.

## Evaluator Metrics

- Key finding: v32 did not expand the hard-eval frontier.
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_step_003000000.ckpt`
- Evidence: 19% success, 7.208s mean successful time, 81% crash, 0% timeout,
  and 1.66 mean gates.
- Comparison: loop097 global best remains 20% success, 7.055s mean successful
  time, 80% crash, and 1.66 mean gates.
- Failure distribution: 81 contact failures, all classified as
  bounds_or_ground; failures by target gate were gate0 31, gate1 18, gate2 28,
  and gate3 4.
- Recommended decision: `change_reward_or_training_numbers`; do not continue
  v32 unless the main agent explicitly chooses to test the step-count concern.

## W&B/PPO Diagnostics

- Key finding: PPO looked stable but mostly inert; W&B reward improvement did
  not convert into hard-eval success.
- Evidence: `approx_kl` fell near zero, `clipfrac` was 0, entropy stayed near
  4.19, explained variance stayed around 0.76, and value loss was high but not
  exploding.
- Race metrics stayed flat: passed-gate, finished, crashed, and gate-stage
  rates did not materially move.
- Hard eval by checkpoint was 16%, 16%, 19%, 18%, and 16% success.
- Reward-number tuning is not justified from W&B alone.
- Recommended decision: `launch_named_structural_lane`, preferably a
  gate-phase reset curriculum or gate-acquisition training-distribution lane.

## Structure/Research Synthesis

- Key finding: keep v32 alive for one bounded continuation, not reward tuning.
- Evidence: loop099 nearly matched the loop097 frontier after only a short 5M
  privileged-Critic screen and used the intended v5 Actor plus privileged
  Critic structure.
- Recommended decision: `continue_same_hypothesis`.
- Risk condition: if a longer v32 maturation fails to beat 20% success or
  materially expand mean gates beyond 1.66, stop v32 and move to a named
  normalization, gate-phase reset, curriculum, PLR, or other
  training-distribution support lane.

## Main-Agent Use

The reviews disagree. The main-agent decision should make the tradeoff explicit:
loop099 is not a success, but one bounded v32 continuation from the best 3M
checkpoint is a direct test of whether the first v32 screen was too short. If
that continuation fails, do not keep repeating v32 or reward-number tweaks.
