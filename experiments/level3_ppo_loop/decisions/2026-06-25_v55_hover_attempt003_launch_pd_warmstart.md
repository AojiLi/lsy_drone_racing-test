# v55 Tracker Decision: Launch Hover PD Warmstart

Date: 2026-06-25

Decision: `launch_tracker_structural_fix`

Stage: `hover`

Approved next lane:

```text
v55_tracker_hover_pd_warmstart_attempt004
```

## Decision

Attempt003 failed the hover stage gate. The next structural move is to add a
hover PD behavior-cloning warmstart:

```text
PD hover teacher -> supervised actor BC checkpoint -> hover eval -> PPO fine-tune
```

Do not unlock `point_hold`.
Do not continue the same PPO-from-scratch hover setup.
Do not switch rollout horizon before testing the warmstart.

## Why

Attempt003 final checkpoint was safe but far from target:

```text
success_rate = 0.0
crash_rate = 0.0
mean_position_error_m = 1.1500089168548584
p90_position_error_m = 1.3974599838256836
mean_speed_mps = 0.23614981770515442
```

W&B showed modest KL/clip but near-zero explained variance and large value
loss. The policy is not learning a reliable local servo from PPO exploration.

A simple PD hover controller can solve the same free-space hover dynamics, so
the next experiment should teach that local servo mapping directly instead of
asking PPO to discover it from scratch.

## Required Implementation

Add a small hover BC script that:

- collects free-space hover tracker observations from a PD teacher;
- computes normalized `[roll, pitch, yaw, thrust]` teacher actions;
- trains the tracker actor mean with supervised MSE;
- saves a normal tracker checkpoint readable by existing evaluator/trainer.

Then run:

1. BC checkpoint training and hover evaluation.
2. If BC checkpoint is finite and materially better than attempt003, run PPO
   fine-tune from it with:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 1000000
--checkpoint-interval 250000
--initial-model-path <BC checkpoint>
```

Use W&B run:

```text
v55_tracker_hover_pd_warmstart_attempt004
```

If BC itself cannot improve hover metrics, hold and inspect the teacher/action
mapping before another PPO run.
