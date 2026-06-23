# Level3 Post-Run Decision: Reject v32, Launch v33 Gate-Phase Reset Curriculum

## Trial

- Trial id: `level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m`
- Analysis report: `experiments/level3_ppo_loop/analysis/level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m_analysis.md`
- W&B run: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m
- Best loop100 checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m/level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m_final.ckpt`
- Hard-eval success rate: 19%
- Mean successful time: 7.304s
- Crash rate: 81%
- Mean gates: 1.65
- Target met: no

## Subagent Findings

- `evaluator_metrics`: stop v32. loop100 did not beat loop097 global best
  20% success / 1.66 mean gates / 80% crash on unchanged `config/level3.toml`.
- `wandb_ppo_diagnostics`: PPO was stable but weak; reward improved without
  gate/finish conversion. Continue neither v32 nor reward-number tuning.
- `structure_research_synthesis`: launch `v33_gate_phase_reset_curriculum`.
  The failure is now more likely training distribution and gate acquisition
  exposure than privileged value estimation alone.

## Main-Agent Decision

Selected decision: `launch_named_structural_lane`

Lane:
`v33_gate_phase_reset_curriculum_from_loop097_12m`

## Rationale

- Local evaluator evidence: loop100 peaked at 19% success and did not pass the
  v32 promotion gate of success above 20% or stable mean-gate expansion beyond
  1.66 with lower crash.
- W&B evidence: training reward improved, but `race/passed_gate_rate`,
  `race/finished_rate`, and crash signals did not convert.
- PPO/training evidence: KL and clip fraction were very small, value loss
  decreased, and explained variance stayed usable. This does not look like an
  unstable PPO failure; it looks like insufficient useful gate-acquisition
  training states.
- Structural evidence: the standing framework places gate-phase reset
  curriculum after asymmetric privileged Critic. v32 has now failed its
  bounded maturation test.
- External research evidence: no new external source is introduced in this
  packet; this follows the existing framework packet and local hard-eval
  evidence.

## Next Lane

The next training chunk should use the new v33 training-only reset curriculum:

- final hard eval remains unchanged `config/level3.toml`;
- training config remains `level3.toml`;
- deployed Actor observation remains v5 local-obstacle history;
- reward numbers and PPO numbers remain the loop052 nominal baseline;
- initial checkpoint returns to loop097/v31d 12M global best;
- 45% of training episodes reset near target-gate approach phases;
- 55% of training episodes keep normal Level3 resets;
- no Level3 track geometry or acceptance randomization is changed;
- screen for 10M with 1M checkpoints and milestone hard eval at 1M, 2M, 3M,
  5M, 8M, and 10M.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v33_gate_phase_reset_curriculum_from_loop097_12m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_100_structural_v32_privileged_critic_mature_loop099_3m_to_18m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_pasted_structural_update.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop100_reject_v32_launch_v33_gate_phase_reset_curriculum.md
```

## Boundaries

- Do not modify Level3 track geometry or randomization to improve the metric.
- Final acceptance must be hard eval on unchanged `config/level3.toml`.
- If v33 does not beat 20% success or materially improve mean gates/crash, do
  not continue it blindly; write a new decision packet for PLR, GRU, or another
  named structural lane.
