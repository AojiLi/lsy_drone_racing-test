# Level3 Post-Run Decision: Reject v33 As-Is, Launch v34 Train-Pool PLR

Decision: `launch_named_structural_lane`

Approved structural hypothesis:

```text
v34_lowprob_train_pool_plr_from_loop101
```

## Evidence

loop101 tested v33 gate-phase reset curriculum from the loop097 12M checkpoint
for 10M steps on unchanged `config/level3.toml`.

Best loop101 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt`
- success: `20/100`
- mean gates: `1.69`
- crash: `80/100`
- mean successful time: `6.873s`

Milestone evidence:

| Checkpoint | Success | Mean Gates | Crash | Success Time |
| --- | ---: | ---: | ---: | ---: |
| 1M | 19% | 1.70 | 81% | 7.204s |
| 2M | 12% | 1.59 | 88% | 6.803s |
| 3M | 9% | 1.53 | 91% | 7.496s |
| 5M | 16% | 1.59 | 84% | 6.918s |
| 8M | 19% | 1.81 | 81% | 7.223s |
| 9M | 16% | 1.62 | 84% | 7.075s |
| final | 20% | 1.69 | 80% | 6.873s |

This ties the old 20% success frontier and slightly improves mean gates/time,
but it does not reduce crash rate or move toward the 60% target. The 8M
mean-gate signal is useful, but it did not convert to more finishes.

## Review Synthesis

- `evaluator_metrics`: stop v33 as-is. The result is a seed reshuffle, not a
  real frontier break.
- `wandb_ppo_diagnostics`: stop v33 as-is. PPO was stable but conservative;
  W&B race signals did not meaningfully convert. Reject the analyzer's generic
  reward-number command.
- `structure_research_synthesis`: one bounded v33 continuation is defensible,
  but if v33 stops, PLR should come before GRU.

Main-agent synthesis: do not blindly continue v33. Move to the next framework
stage, but keep it conservative and training-only.

## Approved v34 Lane

v34 is an offline prioritized-level-replay screen:

- train config remains unchanged `config/level3.toml`;
- final hard eval remains unchanged `config/level3.toml`;
- deployed Actor observation remains v5 local-obstacle history;
- reward numbers and PPO numbers remain the loop052 nominal baseline;
- initial checkpoint is loop101 final;
- v33 gate-phase reset curriculum remains enabled at `0.45`;
- add training-only `track_generator_profile=v34_lowprob_train_pool_bounds_plr`;
- replay probability is `0.08`, so normal random Level3 tracks remain `0.92`;
- replay seeds come only from train-pool bounds/ground failures;
- dev_seen, validation_unseen, and final_locked seeds must not appear in the
  replay profile.

This is not online dynamic PLR. It is a bounded offline PLR screen using
train-pool evidence only. If it does not beat the 20% frontier or materially
raise mean gates with crash no worse than 80%, stop this lane and write a new
packet for online PLR/competence gating or GRU.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v34_lowprob_train_pool_plr_from_loop101 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_pasted_structural_update.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop101_reject_v33_launch_v34_train_pool_plr.md
```

## Boundaries

- Do not modify Level3 track geometry or randomization to make the task easier.
- Do not train on validation or final seeds.
- Do not add planner, MPC, waypoint policy, seed-replay controller, or
  inference-time safety shield.
- Do not accept W&B reward curves without hard-eval improvement.
- Run one train/evaluate chunk, then analyzer, exactly three reviews, and a new
  main-agent decision packet before any further training.
