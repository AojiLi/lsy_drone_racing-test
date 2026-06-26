# Decision: V60 Bounded Smoke Clean, Continue Same Stage More Steps

Date: 2026-06-26T21:15:09+02:00

Decision type: `continue_same_stage_more_steps`

## Decision

The bounded v60 smoke passed its plumbing and semantics purpose. Continue the
same stage with a real bounded maturation chunk before judging learning.

Do not launch planner-driven Level3 long training yet. Do not launch v59 local
safety reflex yet.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-26_v60_reference_command_no_gate_reward_bounded_smoke.md
```

Smoke facts:

- Trainer completed and logged to W&B.
- Checkpoint was saved and loaded by the evaluator.
- Metadata confirms `reference_command_no_gate_reward`.
- Metadata confirms clean actor layout
  `level3_reference_tracker_command_v3` with `56` dimensions.
- Gate/aperture reward coefficients are zero.
- Evaluator reported `checkpoint_backed=true` and `all_finite=true`.
- Gate checker did not unlock the stage, which is expected after only `4096`
  timesteps.
- `config/level3.toml` was not changed.

## Interpretation

This smoke can reject broken code, broken W&B logging, broken checkpoint
metadata, broken evaluator loading, or non-finite action behavior. It cannot
reject PPO learning quality because it used only `4096` timesteps.

The failed stage-gate metrics are therefore learning-maturation evidence, not a
reason to abandon v60:

```text
success_rate = 0.0
crash_rate = 1.0
position errors still too high
brake/hold speed slightly too high
```

## Next Action

Prepare a bounded v60 maturation run:

```text
stage: reference_command_no_gate_reward
config: config/level3_tracker_free_space.toml
observation layout: level3_reference_tracker_command_v3
budget: 8M timesteps by default
rollout geometry: 1024 envs x 32 steps
checkpoint interval: 1M
W&B: enabled
```

After maturation, evaluate milestone checkpoints and run the stage gate. If the
stage still fails, use exactly three analysis reviews before changing reward,
curriculum, PPO hyperparameters, observation layout, or budget.
