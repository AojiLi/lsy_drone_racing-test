# Decision: Reject V49 Same-Schedule Maturation, Launch V50 Hidden512 Update Pressure

Decision: `launch_named_structural_lane`

Trial resolved:
`level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery_analysis.md`

Subagent review packet:
`experiments/level3_ppo_loop/analysis/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery_subagent_reviews.md`

Research packet:
`experiments/level3_ppo_loop/research/2026-06-24_level3_v50_hidden512_update_pressure_plan.md`

Next structural lane:
`v50_hidden512_update_pressure_conversion_from_loop110_3m`

## Decision

Reject v49 as-is. Do not continue loop119/loop120 checkpoints toward 90M or
120M with the same `5e-5`, annealed, high-entropy schedule.

Do not abandon the hidden512 family yet. Launch one named hidden512 PPO-number
follow-up:

```text
v50_hidden512_update_pressure_conversion_from_loop110_3m
```

v50 starts again from loop110/v39 3M, expands to hidden_dim `512` via
block-copy warm-start, keeps v5 observation and v39 reward numbers, and changes
only PPO/training numbers to test whether the larger policy needs stronger,
sustained update pressure.

## Rationale

loop120 gave the effective v49 60M read after recovering loop119's 45M
checkpoint:

- best checkpoint: loop120 recovery `5M`;
- success rate: `15%`;
- mean gates: `1.50`;
- crash rate: `85%`;
- mean successful time: `6.741s`;
- later milestones drifted to `14%` and then `13%` success.

The old frontier remains around `21%` success and `1.66` mean gates. Since
loop120 has non-zero gate progress, there is no obvious fatal hidden512 wiring
failure. But the downward recovery trend and W&B traces make same-hypothesis
maturation unattractive.

The important W&B diagnosis is weak PPO movement:

- `losses/approx_kl` ended near `0.000002`;
- `losses/clipfrac` stayed `0.0`;
- `losses/policy_loss` was near zero;
- entropy rose to about `5.38`;
- gate/finish metrics did not convert.

So the next hidden512-family experiment should test update pressure before
moving to observation, memory, or curriculum.

## V50 Parameters

Changed versus v49:

- `learning_rate`: `5e-5 -> 1e-4`;
- `anneal_lr`: `True -> False`;
- `update_epochs`: `5 -> 8`;
- `clip_coef`: `0.26 -> 0.30`;
- `ent_coef`: `0.02 -> 0.005`;
- `vf_coef`: `0.7 -> 0.5`;
- `target_kl`: `0.03 -> 0.05`;
- `train_timesteps`: one bounded `30M` screen;
- checkpoints/eval milestones: `5M`, `10M`, `15M`, `20M`, `30M/final`.

Unchanged:

- train config: `config/level3.toml`;
- hard eval config: `config/level3.toml`;
- observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- policy: 2-layer Tanh MLP, hidden_dim `512`;
- reward structure and v39 reward numbers;
- deployment: observation/history -> PPO Actor -> roll/pitch/yaw/thrust;
- no inference-time planner, teacher, shield, rule controller, or replay.

## Guardrails

- Do not edit `config/level3.toml` track geometry, gates, obstacles, or
  randomization.
- Do not use loop120 final as the next starting checkpoint.
- Do not count W&B reward curves as success; the hard evaluator decides.
- Do not run `--max-iterations > 1`.
- After v50 completes, run the analyzer, collect exactly three subagent
  reviews, and write a main-agent decision packet before any next training.

## Promotion / Rejection

Continue v50 toward 60M only if a checkpoint shows one of:

- success near or above `18%` with mean gates `>=1.55`;
- hard-eval mean gates improve while W&B passed-gate or finished metrics rise;
- update pressure becomes non-degenerate without crash/tilt blow-up.

If v50 stays below `16%` success and below `1.50` mean gates, stop PPO-number
tuning and launch the required hidden512 observation, memory, or curriculum
follow-up.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v50_hidden512_update_pressure_conversion_from_loop110_3m \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-24_level3_v50_hidden512_update_pressure_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-24_loop120_reject_v49_recovery_launch_v50_hidden512_update_pressure.md
```
