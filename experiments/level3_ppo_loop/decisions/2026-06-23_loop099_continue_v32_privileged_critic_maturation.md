# Decision: Continue v32 Privileged Critic Maturation

Decision: `continue_same_hypothesis`

## Trial

- Trial id:
  `level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_analysis.json`
- Subagent review packet:
  `experiments/level3_ppo_loop/analysis/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_subagent_reviews.md`
- W&B run:
  https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_step_003000000.ckpt`
- Hard-eval success rate: 19%
- Mean successful time: 7.208s
- Crash rate: 81%
- Mean gates: 1.66
- Target met: no

## Subagent Findings

- `evaluator_metrics`: v32 did not beat the loop097 global best. It matched
  mean gates but was slightly worse on success, time, and crash. Recommended
  not maturing v32 unless the main agent explicitly chooses to test the
  step-count concern.
- `wandb_ppo_diagnostics`: PPO was stable but mostly inert. Training reward
  improved without hard-eval conversion. Immediate reward-number tuning is not
  justified from W&B alone; a gate-acquisition structural lane is the fallback.
- `structure_research_synthesis`: continue v32 once as a bounded maturation.
  The 5M screen nearly matched the frontier and is too short to conclusively
  reject the privileged-Critic hypothesis.

## Main-Agent Decision

Selected decision: `continue_same_hypothesis`

The next chunk will continue the same v32 privileged-Critic hypothesis from the
best loop099 checkpoint, not repeat the original 5M screen from loop097. This
directly tests whether the first v32 run was too short while keeping the
experiment bounded.

## Rationale

- Local evaluator evidence: loop099 did not improve the frontier, but its 3M
  checkpoint matched the best known mean-gate depth and remained near the 20%
  success frontier.
- W&B evidence: update metrics did not show an obvious PPO blow-up, but W&B
  reward conversion was weak. This argues against reward-number tuning as the
  immediate next move.
- PPO/training evidence: the deployed Actor path, reward numbers, PPO numbers,
  rollout geometry, disabled normalization, and privileged-Critic mode should
  stay fixed for this continuation.
- Structural evidence: the framework allows structural search, but v32 has
  only received one short screen. A bounded continuation is cheaper and more
  diagnostic than jumping directly to reward changes or an unimplemented v33.
- External research evidence: the framework packet still ranks privileged
  Critic before gate-phase reset, PLR, GRU, reward-number tuning, and speed.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v32_asymmetric_privileged_critic_maturation_from_loop099_3m_to_18m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_pasted_structural_update.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop099_continue_v32_privileged_critic_maturation.md
```

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on unchanged `config/level3.toml`.
- Do not change observation layout, reward numbers, PPO hyperparameters, Actor
  architecture, or inference controller in this continuation.
- If this maturation does not beat 20% success or materially expand mean gates
  beyond 1.66 with lower crash or new success seeds, stop v32 and write a named
  v33 support packet for gate-phase reset/curriculum or another
  training-distribution change before any further training.
