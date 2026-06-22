# v30 Semantics Audit Packet

Decision: `hold_for_more_analysis`

Status: approved for code audit and tests only. This packet does not authorize
training.

## Verdict

Create a v30 semantics-audit lane before launching any new Level3 training. The
next train/evaluate chunk remains blocked until deterministic loop052 checkpoint
parity passes on final-target `level3.toml` with `validation_unseen` seeds
101-200.

This packet is intentionally not a reward, observation, controller, replay, or
network hypothesis. Its purpose is to prove that the training and evaluation
semantics are trustworthy before another long run spends GPU time.

## Why This Comes Before Training

Recent loops have churned around the loop052 frontier without converting W&B
signals or replay/retention signals into better hard-eval success. That pattern
can be caused by a real controller limitation, but it can also be amplified by
semantic mismatches that make PPO learn from one transition/action distribution
while evaluation measures another.

The v30 audit must therefore check these semantics before another training
launch:

- action clipping and PPO log-prob mismatch;
- finish same-step termination;
- finish bonus awarded exactly once;
- no terminal-to-reset dummy transition in the collected rollout;
- per-slot `RaceObservation` history and `last_action` reset at episode
  boundaries;
- observation delay buffers reset from the true post-reset observation for done
  slots;
- real termination reason logging instead of geometry-only endpoint guessing.

## Current Evidence

The current Level3 actor uses a bounded mean followed by an unconstrained Normal
sample. The environment wrappers then clip normalized actions to `[-1, 1]`.
That means PPO can record the log-probability of the sampled action while the
simulator actually receives a clipped action.

The current race-core step saves `marked_for_reset` before stepping and uses
that previous flag for autoreset. That makes the transition after a terminal
condition susceptible to an extra dummy terminal-to-reset step.

The current race-core step updates disabled drones before updating target gates.
Passing the last gate can therefore set `target_gate = -1` after the disabled
check, delaying finish termination by one step.

The current flattened Level3 observation wrapper resets history and
`last_action` only on full environment reset. It does not reset per vector slot
when one slot terminates inside a vector rollout.

The current evaluator taxonomy can label far-away final positions as
`bounds_or_ground` by geometry fallback. That is useful as a crash-location
guess, but it is not a true environment termination reason.

## Required Tests

Implement focused tests for:

- detecting the action clipping/log-prob mismatch;
- finish same-step termination;
- finish bonus exactly once;
- no terminal-to-reset dummy transition;
- per-slot `RaceObservation` history/last_action reset;
- observation delay reset behavior at done boundaries;
- termination reason logging.

Known current semantic failures may be marked `xfail(strict=True)` while they
are audit gates. When the implementation is fixed, remove the matching xfail
and require the test to pass normally.

## Deterministic Parity Gate

Before any v30 training starts, run deterministic loop052 checkpoint parity on
the validation split:

```bash
pixi run -e gpu python scripts/evaluate_level2_selected_ppo.py \
  --config level3.toml \
  --seed-file experiments/level3_ppo_loop/seed_manifests/validation_unseen_101_200.txt \
  --seed-split-name validation_unseen \
  --inference-module ppo_level3_inference \
  --failure-taxonomy \
  --out-prefix experiments/level3_ppo_loop/diagnostics/v30_loop052_parity_validation_unseen \
  lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt
```

The first old-inference run on `level3.toml` establishes the final-target
loop052 baseline. Any repaired inference path or squashed-Gaussian zero-update
path must then reproduce that `level3.toml` baseline within the declared
deterministic tolerance:

- success count and success seed set exactly match;
- max per-step deterministic action difference `< 1e-6`;
- crash rate, mean gates, and mean successful time match within CSV precision.

Do not compare this `level3.toml` parity baseline to the older `level3_dr.toml`
0.20 validation anchor; `level3_dr.toml` is now treated as a domain-randomized
sim-to-real robustness config, not the final acceptance target.

If parity fails, stop and diagnose inference/evaluation semantics. Do not launch
training to "average it out."

## Rejected Actions

- Launch loop091 or any other new training chunk from this packet.
- Continue reward tuning while the audit gates are unresolved.
- Use `final_locked` seeds.
- Modify `config/level3.toml` geometry or randomization.
- Treat geometry-only `bounds_or_ground` as a real termination reason.
- Accept W&B reward curves as a substitute for hard-eval parity.

## Next Allowed Work

Allowed:

- add or improve audit tests;
- add deterministic parity tooling;
- fix semantic bugs exposed by the audit;
- rerun focused tests and deterministic loop052 validation parity.

Blocked until parity passes:

- any Level3 PPO training launch;
- any new structural/reward/network/replay lane.
