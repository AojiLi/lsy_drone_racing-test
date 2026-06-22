# Launch v30 End-to-End PPO Corrected Action and Episode Semantics

Decision: `launch_named_structural_lane`

Status: conditionally approved. Do not launch training until the v30 semantic
fixes and loop052 deterministic parity gate pass.

## Thesis

Loop090 does not prove that end-to-end PPO is the wrong approach. It proves that
the recent reward-number, static seed replay, fixed offline teacher-KL, and
short checkpoint-continuation directions did not convert to hard-eval behavior.

The next lane keeps the deployment policy strictly end-to-end:

```text
Level3 observation/history
  -> PPO actor
  -> [roll, pitch, yaw, thrust]
  -> environment
```

No MPC, waypoint planner, upper-level subgoal policy, rule controller, expert
planner, or inference-time safety shield is approved by this packet.

## Locked Baseline

The first v30 experiments must isolate implementation semantics. Keep these
fixed:

- initial checkpoint: loop052 final;
- actor input: loop052 v5 observation layout;
- actor output: normalized roll/pitch/yaw/thrust command;
- network: 2x256 MLP;
- reward structure and reward numbers: loop052 values;
- PPO learning rate, gamma, GAE, clip, epochs, minibatches: loop052 values;
- hard eval: unchanged `config/level3_dr.toml`;
- teacher KL: disabled;
- static success/failure seed replay: disabled;
- final_locked seeds: not used.

## Required Semantic Fixes

Before training, implement and test:

- same-step finish termination;
- finish bonus awarded exactly once on the finish transition;
- no terminal-to-reset dummy transition in rollouts;
- per-slot reset of `RaceObservation` history and `last_action`;
- observation delay buffers reset from true post-reset observations for done
  slots;
- real termination reason logging;
- deterministic loop052 old-vs-new inference parity on
  `validation_unseen` seeds 101-200.

The existing v30 audit gate remains authoritative:

`experiments/level3_ppo_loop/decisions/2026-06-22_v30_semantics_audit_approved.md`

## v30-A

Name:

`v30_episode_semantics_only_2m`

Purpose:

Test whether corrected episode/reset/finish semantics alone improves or
stabilizes the loop052 frontier.

Training:

- 3 independent training seeds;
- 2M steps per seed;
- checkpoint interval 0.5M;
- validation on `validation_unseen` 101-200 for every selected checkpoint;
- W&B project `ADR-PPO-Racing-Level3`.

## v30-B

Name:

`v30_squashed_gaussian_episode_semantics_2m`

Purpose:

Test corrected episode semantics plus a bounded PPO policy:

```text
u ~ Normal(mu, sigma)
a = tanh(u)
log pi(a|s) = log Normal(u; mu, sigma) - sum(log(1 - tanh(u)^2 + eps))
```

The zero-update deterministic action from the loop052 checkpoint must match the
old inference path with max per-step action error `< 1e-6` before training.

## Promotion Gate

Do not promote from a single lucky training seed. Across the 3 training seeds:

- median success rate `>= 0.25`;
- at least one checkpoint success rate `>= 0.30`;
- crash rate `<= 0.70`;
- mean gates `>= 1.60`.

If v30-A and v30-B both fail this gate, hold for diagnosis before considering
dynamic PLR or gate-phase curriculum.

## Rejected For This Stage

- reward automatic tuning;
- teacher KL;
- static seed replay;
- velocity/subgoal policy;
- MPC, MPCC, waypoint planner, or external expert planner;
- speed optimization before success is near 50%;
- use of `final_locked` seeds.

## Next Stages, Not Yet Approved For Training

If v30 reaches roughly 30% validation success, propose v31 prioritized Level3
track replay. This must stay on-policy PPO: replay chooses training track
instances, not old actions or expert trajectories.

If v31 still leaves gate phase imbalance, propose training-only gate-phase
balanced reset. Deployment remains a single PPO actor from observation/history
to roll/pitch/yaw/thrust.

Recurrent PPO can be retried only after v30 reset semantics are fixed, because
the previous GRU result may have been contaminated by hidden-state/reset bugs.
