# Decision: v62c Needs Value/Velocity Stabilization Before Long Maturation

Date: 2026-06-27

## Decision

```text
change_tracker_curriculum_or_reward
```

Do not continue v62c directly to 60M+ and do not use the final checkpoint as the
default resume point.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62c_milestone_value_velocity_review.md
```

Checkpoint review:

- best overall checkpoint is `7M`;
- best checkpoint path is
  `lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl`;
- best reward and balanced score occur at `7M`;
- best trained-checkpoint velocity error also occurs at `7M`;
- best position/cross-track checkpoint is `2M`, but its velocity error is worse.

Velocity finding:

- initial velocity error under the same 16-rollout protocol: `0.6465`;
- `1M` velocity error: `0.8826`;
- no trained checkpoint returns below the initial velocity error;
- within the trained curve, `7M` is the least-bad velocity point and `8M`
  starts the post-peak worsening.

Final checkpoint finding:

- final reward: `-5.6864`, worse than `7M` at `-4.8459`;
- final position error: `0.6899`, worse than `7M` at `0.6573`;
- final cross-track error: `0.5718`, worse than `7M` at `0.5214`;
- final velocity error: `0.8915`, worse than `7M` at `0.7397`;
- final balanced score: `-8.6510`, worse than `7M` at `-7.5365`.

## Interpretation

The v62c tanh/JAX backend is still valid: it improved spatial tracking compared
with the untrained policy. The problem is that the current objective/training
setup teaches the tracker to get closer to the reference path while degrading
speed obedience.

That is not acceptable for the planner/tracker plan. The upper planner will
need the bottom PPO to obey:

```text
slow down
hold/brake
low-speed-through
recover speed gradually
```

If velocity obedience is already worse from `1M`, longer training alone is
unlikely to fix the core issue.

## Next Action

Launch a narrow support lane:

```text
v62d_value_velocity_stabilization_support
```

This is a builder/checker-gated support step, not a long training step.

Required scope:

- keep `tanh_squashed_gaussian`;
- keep clean observation layout `level3_reference_tracker_command_v3`;
- keep gate/obstacle/planner-phase actor inputs absent;
- keep gate-pass, aperture, finish, race-progress, and stage-progress rewards
  absent;
- preserve `config/level3.toml` and `config/level3_tracker_free_space.toml`;
- inspect or implement value/return normalization, critic target scaling, or
  another critic-stability fix;
- improve generic command-velocity diagnostics and, only if justified, adjust
  generic velocity/along-speed reward weights;
- after checker approval, run a bounded follow-up using `7M` as the preferred
  diagnostic resume checkpoint.

## Guardrails

- Do not start 60M+ v62c maturation from final.
- Do not call the `7M` checkpoint a passed tracker policy.
- Do not add Level3 gate semantics to the bottom tracker.
- Do not modify the Level3 target track.
