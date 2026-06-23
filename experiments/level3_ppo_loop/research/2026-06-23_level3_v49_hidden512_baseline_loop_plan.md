# Level3 V49 Hidden512 Baseline Loop Plan

Status: approved structural plan for the next capacity-family baseline after
loop118/v48.

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

The corrected Level3 loop has repeatedly plateaued near the same frontier:

- loop107/v37 1M: `21%` success, `1.66` mean gates, `79%` crash.
- loop110/v39 3M: `21%` success, `1.64` mean gates, `79%` crash.
- loop116/v45: `20%` success, `1.60` mean gates, `80%` crash.
- loop117/v47: `20%` success, `1.58` mean gates, `80%` crash.
- loop118/v48: `16%` success, `1.50` mean gates, `84%` crash.

This makes another small contact-reward tweak a weak next move. The user wants
the larger network to become a new loop baseline, then later reward,
observation, curriculum, or GRU changes should be tested inside that larger
network family.

Earlier hidden512 evidence from loop061 was negative, but it came from an older
loop052/v9 branch and reached only `10%` success. It does not answer whether
the current loop110/v39 3M v5 frontier benefits from a controlled 512-wide
warm-start.

## Hypothesis

```text
v49_v5_hidden512_mlp_warmstart_from_loop110_3m
```

A 2x256 v5 MLP may be too small to serve as the base policy for Level3's
randomized gates and obstacles. Instead of mixing capacity with a new reward or
observation structure, v49 isolates capacity:

- same v5 observation;
- same v39 gate-acquisition reward numbers;
- same PPO rollout geometry;
- same hard eval on `config/level3.toml`;
- only change the Actor/Critic hidden width from `256` to `512`.

The checkpoint warm-start should use the existing block-copy path:

```text
loop110/v39 3M 2x256 MLP
  -> allow_hidden_dim_warmstart=True
  -> v49 2x512 MLP
```

## Training Lane

- Initial checkpoint: loop110/v39 3M MLP frontier.
- Train config: unchanged `config/level3.toml`.
- Hard eval config: unchanged `config/level3.toml`.
- Actor: v5 local-obstacle MLP, `mlp_2x_tanh`.
- Critic: same observation MLP.
- Hidden width: `512`.
- Retention: disabled.
- Reward structure: v39 `legacy_staged` gate-acquisition numbers.
- Horizon: one bounded `5M` screen.
- Checkpoints: `1M`, `2M`, `3M`, `4M`, `5M/final`.
- W&B logging: required.

## Follow-Up Loop Policy

If v49 clearly beats the frontier, mature the same hidden512 hypothesis before
switching structure.

If v49 roughly preserves the frontier without degrading, treat its best
checkpoint as the new hidden512 baseline and run follow-up lanes inside this
family:

- hidden512 reward/PPO-number follow-up;
- hidden512 observation variant;
- hidden512 residual-GRU or GRU transfer;
- hidden512 curriculum or training-distribution reshaping.

If v49 regresses, do not immediately reject hidden512. v49 is the bootstrap
screen for a new loop family, not a final capacity verdict. The post-run
decision should normally choose a targeted hidden512 follow-up based on the
failure mode:

- poor gate acquisition: adjust hidden512 reward/PPO numbers;
- gate geometry confusion: add a hidden512 observation variant;
- drift/seed churn: add hidden512 retention or curriculum;
- partial observability: add hidden512 GRU or residual-GRU support.

Do not reject the hidden512 family until at least three evaluated hidden512
family trials exist:

- the hidden512 baseline screen;
- one hidden512 reward/PPO-number follow-up;
- one hidden512 observation, memory, or curriculum follow-up.

The only exception is catastrophic loss of basic ability: near-zero success
with mean gates below `0.50`, or a confirmed wiring/training failure. In that
case, hold for diagnosis instead of silently returning to 2x256.

## Promotion / Rejection Rule

Promote or mature v49 if it shows one of:

- success `>21%`;
- success `>=21%` with mean gates above `1.66` and crash `<=79%`;
- clear success-seed expansion without losing the old frontier.

Accept as a temporary hidden512 baseline if it stays near the frontier without
degradation, even if it does not yet meet the final target.

Hold for diagnosis, not family rejection, if:

- success is near zero;
- mean gates `<0.50`;
- training/evaluation wiring fails;
- checkpoint warm-start metadata is inconsistent.

## Next-Loop Requirement

After v49 completes, run `scripts/analyze_level3_ppo_trial.py`, spawn exactly
three review subagents for evaluator metrics, W&B/PPO diagnostics, and
structure/research synthesis, then write a main-agent decision packet before
any further hidden512 follow-up training. That packet should keep the next move
inside the hidden512 family unless v49 catastrophically loses basic gate
progress or exposes a wiring bug.
