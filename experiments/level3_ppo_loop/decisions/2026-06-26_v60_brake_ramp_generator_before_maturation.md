# Decision: Add Brake Ramp Before v60 8M Maturation

## Decision

Use the v60 dense command generator with explicit pass-to-hold brake ramp
before starting the 8M maturation run.

Allowed next action:

```text
launch_v60_reference_command_no_gate_reward_8m_maturation_with_brake_ramp_dense_generator
```

## Reason

The previous dense generator made references continuous, but the speed command
could still transition too abruptly:

```text
pass_through at cruise speed -> hold_or_brake near zero speed
```

The tracker needs advance notice to slow down. The new generator tapers
pass-through desired speed before the hold point, so the command distribution
matches the intended Level3 planner behavior:

```text
cruise -> decelerate -> hold/align -> low-speed-through -> recover
```

## Guardrails

- Do not modify `config/level3.toml`.
- Do not add gate/aperture/race/finish/progress rewards to v60.
- Do not add gate/obstacle/aperture/planner-phase inputs to the clean v60 actor.
- Keep `level3_reference_tracker_command_v3` at `56` dims.
- Treat tiny smoke runs as plumbing checks only.

## Required 8M Run Shape

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

Evaluate milestone checkpoints before planner integration. If the curve is
still improving at 8M, prefer an evidence-backed same-stage extension before
changing observation, reward, planner, or network.
