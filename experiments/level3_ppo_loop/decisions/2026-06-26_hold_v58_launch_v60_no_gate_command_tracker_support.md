# Decision: Hold V58, Launch V60 No-Gate Command Tracker Support

Decision: launch_tracker_structural_fix

Status: no training launched.

## Decision

Hold the previous `v58_tracker_semantic_planner_reference_training` direction.
Replace it with:

```text
v60_reference_command_tracker_no_gate_reward
```

The new canonical task is:

```text
reference_command_no_gate_reward
```

## Rationale

The bottom PPO tracker should not be trained with gate-like inputs or rewards.
Its core job is to follow planner commands:

```text
short reference horizon
+ desired speed / velocity
+ desired heading
+ generic hold / low-speed / pass-through intent
```

Gate pass and Level3 finish are planner-integration or final-evaluation
outcomes. They should not become bottom-tracker reward.

## Guardrails

- Do not modify `config/level3.toml`.
- Do not add gate-pass, aperture-crossing, finish, race-progress, or
  stage-progress rewards to tracker training.
- Do not make the tracker infer route strategy from target-gate semantics.
- Keep v60 in free space first.
- Use builder/checker before long training.
- Keep old v55/v1 checkpoint loading intact.

## Next Action

Validate v60 support with focused tests and unchanged-track checks. After that,
the next goal can run a bounded v60 smoke, not a long training run.
