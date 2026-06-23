# Level3 Post-Run Decision: Reject v34, Launch v35 Competence-Gated Curriculum

Decision: `launch_named_structural_lane`

Approved structural hypothesis:

```text
v35_competence_gated_gate_phase_curriculum_from_loop101
```

## Evidence

loop102 tested v34 low-probability offline train-pool PLR from the loop101
final checkpoint for 10M steps. It kept the deployed v5 Actor observation,
reward numbers, PPO numbers, rollout geometry, v33 gate-phase reset curriculum,
and unchanged `config/level3.toml` hard eval fixed. The only substantive change
was `track_generator_profile=v34_lowprob_train_pool_bounds_plr` with 8% replay
over train-pool bounds/ground failure seeds.

Milestone evidence:

| Checkpoint | Success | Mean Gates | Crash | Success Time |
| --- | ---: | ---: | ---: | ---: |
| 1M | 17% | 1.59 | 83% | 7.593s |
| 2M | 16% | 1.50 | 84% | 7.658s |
| 3M | 15% | 1.55 | 85% | 7.547s |
| 5M | 16% | 1.57 | 84% | 7.289s |
| 8M | 17% | 1.59 | 83% | 7.665s |
| 9M | 13% | 1.50 | 87% | 7.009s |
| final | 10% | 1.43 | 90% | 7.172s |

The global validation-unseen best remains loop101 final:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt`
- success: `20/100`
- mean gates: `1.69`
- crash: `80/100`
- mean successful time: `6.873s`

v34 therefore failed its promotion gate. It neither beat the 20% success
frontier nor materially expanded mean gates with crash no worse than 80%.

## Review Synthesis

- `evaluator_metrics`: stop v34 as-is. Best loop102 is only `17/100` success,
  `1.59` mean gates, and `83/100` crash; final regresses to `10/100`.
- `wandb_ppo_diagnostics`: PPO did not explode. The run looks like stable but
  ineffective updates with mild negative transfer from the static replay
  distribution. Do not start from loop102 final.
- `structure_research_synthesis`: launch competence-gated curriculum first.
  Do not go directly to GRU or reward-number tuning.

Main-agent synthesis: reject v34 offline PLR. Return to loop101 final and test
whether gate-phase reset pressure can be unlocked gradually based on rollout
competence instead of being fixed at 45% or mixed with static replay.

## Approved v35 Lane

v35 is a competence-gated gate-phase reset curriculum screen:

- train config remains unchanged `config/level3.toml`;
- final hard eval remains unchanged `config/level3.toml`;
- deployed Actor observation remains v5 local-obstacle history;
- Actor architecture remains feed-forward `mlp_2x_tanh`;
- Critic remains same-as-Actor observation;
- reward numbers remain the loop052 nominal baseline;
- PPO hyperparameters and rollout geometry remain unchanged;
- initial checkpoint is loop101 final;
- track generator profile returns to `default`;
- no train-pool replay, validation replay, final-seed replay, planner, MPC, or
  inference-time safety layer is introduced.

The only new behavior is training-only competence gating around the existing
gate-phase reset curriculum:

- max gate-phase reset probability stays `0.45`;
- initial gate-phase reset probability is `0.12`;
- probability increases by `0.02` after a PPO iteration only when rollout
  metrics satisfy:
  - `passed_gate_rate >= 0.0068`;
  - `finished_rate >= 0.0007`;
  - `crashed_rate <= 0.0082`.
- W&B logs `curriculum/gate_phase_reset_prob`,
  `curriculum/gate_phase_reset_next_prob`, and the competence metrics.

## Promotion Gate

Promising enough to continue/mature if any checkpoint reaches:

- success `> 20%`; or
- mean gates `> 1.69` with crash `<= 80%` and no late-checkpoint collapse.

Reject v35 if all evaluated checkpoints stay at or below `17%` success, mean
gates fail to expand, or crash rises to `>= 83%`.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v35_competence_gated_gate_phase_curriculum_from_loop101 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_102_structural_v34_lowprob_train_pool_plr_loop101_10m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_pasted_structural_update.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop102_reject_v34_launch_v35_competence_gated_curriculum.md
```

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Do not train on validation or final seeds.
- Do not change reward numbers, observation layout, PPO hyperparameters, or
  Actor/Critic structure in this lane.
- Do not accept W&B reward curves without hard-eval improvement on
  `config/level3.toml`.
- Run one train/evaluate chunk, then analyzer, exactly three reviews, and a new
  main-agent decision packet before any further training.
