# Decision: Reject V50 As Immediate Move, Launch V51 Planner-Guidance PPO256

Decision: launch_named_structural_lane

Trial resolved:
`level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_analysis.md`

Subagent review packet:
`experiments/level3_ppo_loop/analysis/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_subagent_reviews.md`

Research packet:
`experiments/level3_ppo_loop/research/2026-06-24_level3_v51_planner_guidance_obs_ppo256_plan.md`

Next structural lane:
`v51_planner_guidance_obs_ppo256_from_loop110_3m`

## Decision

Do not continue v50 as the next immediate run. Launch v51:

```text
v5 observation/history
+ deterministic planner-guidance observation features
  -> 2x256 Tanh PPO Actor
  -> roll/pitch/yaw/thrust
```

The planner is used at inference only as observation computation. It does not
produce actions, override actions, act as MPC, provide a safety shield, replay
seed-specific routes, or change the race track.

## Rationale

loop121/v50 fixed the v49 PPO update-pressure failure:

- `approx_kl=0.014064`;
- `clipfrac=0.065216`;
- `policy_loss=-0.013724`;
- entropy fell to `0.63339`.

But hard-eval conversion remained weak. Best loop121 checkpoint:

- checkpoint: `25M`;
- success: `18%`;
- mean gates: `1.56`;
- crash: `80%`;
- timeout: `2%`;
- mean successful time: `6.283s`.

The final checkpoint fell to `15%` success and `1.45` mean gates. The global
best remains loop107/v37 1M at `21%` success and `1.66` mean gates. This makes
another hidden512/PPO-number loop less attractive than changing the information
available to the actor.

The user approved planner-as-observation with planner used at inference to
maximize the chance of passing Level3, while keeping the Level3 track unchanged.
This lane attacks the suspected missing signal: local route intent through gates
and around obstacles.

## V51 Setup

- observation layout:
  `level3_planner_guidance_2obs_local_history_v12`;
- planner version:
  `local_gate_waypoint_obstacle_risk_v1`;
- planner feature dimension: `13`;
- hidden dim: `256`;
- policy arch: `mlp_2x_tanh`;
- train config: unchanged `config/level3.toml`;
- hard eval config: unchanged `config/level3.toml`;
- initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt`;
- warm start:
  append planner channels to v5 and zero-pad new input weights;
- training chunk: `30M`;
- milestone hard eval: `5M`, `10M`, `15M`, `20M`, `30M`.

## Promotion / Rejection

Promote or continue v51 toward `60M` if any checkpoint reaches:

- success `>=25%`; or
- mean gates `>=1.75`; or
- crash `<=75%`; or
- clear new solved-seed coverage with healthy W&B PPO diagnostics.

Hold for planner-feature diagnostics if all milestones stay below:

- success `<16%`; or
- mean gates `<1.50`.

Do not judge v51 only from 1M/5M health checks. Use milestone hard eval and
select the best checkpoint rather than assuming final is best.

## Guardrails

- Do not edit `config/level3.toml` track geometry, gates, obstacles,
  randomization, or validation seed split.
- Do not add planner action output, MPC, waypoint-controller takeover, safety
  shield, static seed replay, or fallback rule controller.
- PPO Actor remains the only action-producing controller.
- After v51 completes, run the analyzer, exactly three review agents, and a new
  main-agent decision packet before any next training chunk.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v51_planner_guidance_obs_ppo256_from_loop110_3m \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-24_level3_v51_planner_guidance_obs_ppo256_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-24_loop121_reject_v50_launch_v51_planner_guidance_obs_ppo256.md
```
