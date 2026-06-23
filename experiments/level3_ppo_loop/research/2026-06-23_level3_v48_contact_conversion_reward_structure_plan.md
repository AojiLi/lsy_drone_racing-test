# Level3 V48 Contact/Conversion Reward Structure Plan

Status: approved structural plan for one bounded screen after loop117/v47.

## Scope

Final acceptance remains hard evaluation on unchanged `config/level3.toml`:

- success rate `>= 0.60`;
- mean successful time `<= 7.0s`;
- no Level3 track geometry, gate layout, obstacle layout, or randomization
  changes.

Deployment remains a single end-to-end PPO Actor:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No teacher, planner, shield, ensemble, waypoint controller, or upper-level
controller is allowed at inference.

## Local Evidence

loop117/v47 tested residual-frontier union retention:

- best checkpoint: `3M`;
- success rate: `20%`;
- mean gates: `1.58`;
- mean successful time: `7.064s`;
- crash rate: `80%`;
- timeout rate: `0%`.

Retention was active:

- teacher KL: `0.049981 -> 0.044482`;
- teacher action MSE: `0.011354 -> 0.010212`;
- teacher agreement: `0.871606 -> 0.890039`;
- sampled batch size: `512`.

This rejects the explanation that residual teacher extraction or retention
sampling was simply broken. The hard-eval failure pattern remains contact-heavy
and concentrated at gate 0 and gate 2. Teacher-like behavior did not expand the
validation success set.

## Hypothesis

```text
v48_v5_contact_conversion_reward_structure_from_loop110_3m
```

The current plateau may be a gate-conversion problem rather than a memory or
retention problem. The policy often approaches gates but fails by contact,
wrong-side geometry, or gate-frame interaction. v48 tests whether separating
gate-frame pressure from missed-gate penalty and rewarding center-plane
conversion improves contact behavior without weakening gate acquisition.

## Training Lane

- Initial checkpoint: loop110/v39 3M MLP frontier.
- Train config: unchanged `config/level3.toml`.
- Hard eval config: unchanged `config/level3.toml`.
- Actor: v5 local-obstacle MLP, `mlp_2x_tanh`.
- Retention: disabled.
- Reward structure: `decoupled_frame_clearance`.
- Horizon: one bounded `5M` screen.
- Checkpoints: `1M`, `2M`, `3M`, `4M`, `5M/final`.
- W&B logging: required.

## Reward Structure Delta

Keep the v39 gate-acquisition scale, but add explicit contact/conversion
pressure:

- `reward_structure=decoupled_frame_clearance`
- `gate_stage_coef=13.0`
- `gate_axis_coef=22.0`
- `gate_front_bonus=8.0`
- `gate_plane_bonus=28.0`
- `gate_bonus=190.0`
- `gate_back_bonus=35.0`
- `finish_bonus=175.0`
- `missed_gate_penalty=8.0`
- `gate_frame_pressure_coef=2.5`
- `wrong_side_penalty=12.0`
- `time_penalty=0.02`

## Promotion / Rejection Rule

Promote only if v48 shows at least one of:

- validation success `>21%`;
- validation success `>=21%` with mean gates above `1.66` and crash `<=79%`;
- lower crash/tilt with no loss of mean gates, suggesting a real contact
  conversion improvement.

Reject if it stays in the `18%-22%` plateau, keeps crash near `79%-80%+`,
lowers mean gates, or improves contact metrics only by making the policy less
willing to approach gates.

## Next-Loop Requirement

After the v48 train/evaluate chunk, run
`scripts/analyze_level3_ppo_trial.py`, spawn exactly three review subagents
for evaluator metrics, W&B/PPO diagnostics, and structure/research synthesis,
then write a new main-agent decision packet before any further training.
