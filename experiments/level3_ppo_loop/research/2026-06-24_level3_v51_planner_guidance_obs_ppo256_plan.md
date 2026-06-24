# V51 Plan: Planner-Guidance Observation + PPO256

## Objective

Launch a named Level3 structural lane that maximizes the chance of passing the
unchanged `config/level3.toml` hard evaluator by adding deterministic local
planner guidance to the PPO observation.

Target remains:

- success rate `>= 60%`;
- mean successful time `<= 7.0s`;
- hard eval on unchanged `config/level3.toml`.

## Why Change Direction

loop121/v50 repaired the hidden512 PPO update-pressure issue, but the best
checkpoint still reached only:

- `18%` success;
- `1.56` mean gates;
- `80%` crash;
- `6.283s` mean successful time.

The global best remains loop107/v37 1M at `21%` success and `1.66` mean gates.
Recent hidden512/reward/retention loops are therefore not showing a route to
`60%`. Successful episodes are already fast enough, so the bottleneck is more
likely route intent, gate/corridor interpretation, and obstacle geometry.

## Structural Hypothesis

Use planner guidance as deployed observation, not as an action controller:

```text
v5 Level3 observation/history
+ deterministic planner-guidance features
  -> 2x256 Tanh PPO Actor
  -> roll/pitch/yaw/thrust
```

The planner computes local route-intent features from the same observed Level3
state available to the controller. It does not modify the race track and does
not output actions.

New observation layout:

`level3_planner_guidance_2obs_local_history_v12`

Planner feature schema, appended to v5:

- local target vector in body frame, clipped to `[-2m, 2m]`;
- desired unit direction in body frame;
- current drone position in the active gate frame;
- obstacle-avoidance vector in body XY;
- nearest obstacle XY clearance;
- desired local speed scalar.

Feature dimension: `13`.

Planner version:
`local_gate_waypoint_obstacle_risk_v1`.

## Warm Start

Start from loop110/v39 3M feed-forward v5 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt`

Because v12 appends planner channels to v5, the existing local-feature warm-start
path can copy v5 input weights and zero-pad new planner-channel input weights.
This preserves the old 2x256 behavior at initialization while allowing PPO to
learn the route-intent channels.

## Training Setup

- train config: `level3.toml`;
- eval config: `level3.toml`;
- hidden dim: `256`;
- policy arch: `mlp_2x_tanh`;
- reward structure: v39/v50 legacy staged gate-acquisition numbers;
- PPO update pressure: v50 settings
  `learning_rate=1e-4`, `anneal_lr=False`, `update_epochs=8`,
  `clip_coef=0.30`, `ent_coef=0.005`, `vf_coef=0.5`, `target_kl=0.05`;
- timesteps: `30M` screening chunk;
- milestone hard eval: `5M`, `10M`, `15M`, `20M`, `30M`;
- W&B project: `ADR-PPO-Racing-Level3`.

## Promotion Gate

Continue the same v51 family toward `60M` if any checkpoint reaches one of:

- success `>= 25%`;
- mean gates `>= 1.75`;
- crash `<= 75%`;
- clear new solved-seed coverage with stable W&B PPO health.

Hold for planner-feature diagnostics if all milestones remain below:

- success `< 16%`; or
- mean gates `< 1.50`.

## Required Diagnostics

Before trusting a v51 training result, verify:

- checkpoint metadata records `planner_guidance.enabled=true`;
- checkpoint metadata records `planner_used_at_inference=true`;
- train/inference observation parity covers the `planner_guidance` slice;
- hard eval remains on unchanged `config/level3.toml`;
- W&B tracks PPO health and race conversion:
  `approx_kl`, `clipfrac`, entropy/action std, value loss, explained variance,
  `race/passed_gate_rate`, `race/finished_rate`, `race/crashed_rate`,
  `race/gate_stage`, and hard-eval success/mean gates/crash.

## Guardrails

- Do not edit `config/level3.toml` geometry, gates, obstacles, randomization, or
  hard-eval seed split.
- Do not use the planner as MPC, direct action source, residual action source,
  safety shield, static seed replay, or fallback controller.
- PPO Actor remains the only action-producing controller.
- Any later residual planner, imitation, or safety-shield idea requires a new
  named structural packet.
