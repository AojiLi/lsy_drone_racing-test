# Decision: Use Dense Planner-Like v60 Command Generator Before Maturation

## Decision

`v60_reference_command_tracker_no_gate_reward` should use the new dense
planner-like command generator before any 8M maturation run.

Allowed next action:

```text
launch_v60_reference_command_no_gate_reward_8m_maturation_with_dense_command_generator
```

## Reason

The previous v60 reward was clean, but the generator still risked teaching the
tracker to chase sparse points. The updated generator now gives PPO the actual
driving instruction:

```text
short rolling horizon + desired velocity + desired speed + desired heading
```

For moving commands, velocity follows `current -> lookahead`. For brake/hold,
the horizon is nearly stationary and desired velocity is zero.

## Guardrails

- Do not modify `config/level3.toml`.
- Do not add gate/aperture/race/finish/progress rewards to v60.
- Do not add gate/obstacle/aperture/planner-phase inputs to the clean v60 actor.
- Keep old v1/v2/v55 checkpoint compatibility.
- Treat tiny smoke runs as plumbing checks only.

## Required 8M Run Shape

Use the tracker skill budget for the command stage:

```text
task: reference_command_no_gate_reward
config: config/level3_tracker_free_space.toml
observation_layout: auto -> level3_reference_tracker_command_v3
reward_model: reference_command_reward
num_envs: 1024
num_steps: 32
total_timesteps: 8_000_000
checkpoint_interval: 1_000_000
wandb: enabled
```

Evaluate milestone checkpoints before planner integration. If the default 8M
chunk is still improving but below gate, prefer an evidence-backed same-stage
extension before changing observation, reward, planner, or network.
