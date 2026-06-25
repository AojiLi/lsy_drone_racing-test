# v55 Hover Attempt002 Analysis

Date: 2026-06-25

Stage: `hover`

Run: `v55_tracker_hover_vector1024_attempt002`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/ju8co9w8`

## Training

Command family:

```text
task = hover
config = level3_tracker_free_space.toml
num_envs = 1024
num_steps = 32
total_timesteps = 1000000
checkpoint_interval = 250000
hidden_dim = 256
```

Actual final global step was `983040`, because the trainer runs complete PPO
batches of `1024 x 32 = 32768` environment steps.

## Milestone Evaluation

| Checkpoint | Success | Crash | Mean position error | P90 position error | Mean speed | Mean action delta |
|---|---:|---:|---:|---:|---:|---:|
| `250k` | `0%` | `40%` | `0.6681m` | `0.6511m` | `0.0296m/s` | `0.0020` |
| `500k` | `0%` | `0%` | `0.6510m` | `0.6511m` | `0.0034m/s` | `0.00086` |
| `750k` | `0%` | `100%` | `0.6547m` | `0.6513m` | `0.0051m/s` | `0.0026` |
| `final` | `0%` | `100%` | `0.7345m` | `0.6515m` | `0.3019m/s` | `0.1726` |

Best diagnostic checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/v55_tracker_hover_vector1024_attempt002_step_000500000.ckpt
```

It passed finite/checkpoint/crash/speed/smoothness checks, but failed the hover
gate because `success_rate=0`, `mean_position_error_m=0.65095`, and
`p90_position_error_m=0.65108`.

## Diagnosis

The policy learned a stable near-stationary behavior, not hover tracking.
At `500k`, all 20 evaluated episodes were finite, did not crash, and timed out
at 500 steps with almost identical final error around `0.651m`.

The root cause is that the current `hover` curriculum was effectively a ground
takeoff task with a hover reward:

- `config/level3_tracker_free_space.toml` starts the drone near `z=0.01`.
- `ReferenceTrajectoryGenerator.reset` puts the hover anchor around `z=0.65`.
- `_hover_reference` used `desired_speed=0.0` even when far from the anchor.
- reward was dense negative terms plus a small crash penalty, so early crash or
  near-idle behavior could be easier than learning a controlled climb.

W&B confirms this: `tracker/pos_error` stayed far from the gate threshold,
while easy terms like heading and speed improved. Late PPO updates became
unstable: the run regressed from `0%` crash at `500k` to `100%` crash at
`750k/final`.

This is not a pure undertraining result and not an evaluator mismatch.

## Three-Review Synthesis

- `tracker_eval_metrics`: best is `500k`; it is safe and smooth but does not
  move to the hover target.
- `tracker_wandb_ppo`: reward/termination scaling lets early failure compete
  with long survival; position error plateaued while PPO became unstable late.
- `tracker_structure_research`: change the hover curriculum/initialization and
  reference semantics before another training chunk.

## Result

Stage gate: failed.

Next action: launch a builder/checker-gated structural fix named
`v55_hover_airborne_error_curriculum_attempt003`.
