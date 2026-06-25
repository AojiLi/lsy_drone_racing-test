# PPO Reference Tracker Training Notes

This reference records durable guidance for the Level3 low-level PPO reference
tracker. Read it before changing tracker observation, reward, curriculum,
training schedule, or qualification gates.

## Core Lesson

Train the bottom policy as a trajectory-following servo first, not as a full
Level3 racer. The upper planner should decide where to go and when to slow
down. The PPO tracker should turn a short reference horizon into stable
roll/pitch/yaw/thrust actions.

Do not judge the tracker first by Level3 finish rate. Judge it by independent
tracking metrics on held-out reference tasks, then use unchanged
`config/level3.toml` as planner-integration smoke.

## Source-Backed Patterns

- DATT trains a quadrotor trajectory tracker in simulation using RL for
  arbitrary, potentially infeasible trajectories under disturbances, and its
  public repo separates task/reward from randomized environment configuration:
  https://proceedings.mlr.press/v229/huang23a.html and
  https://github.com/KevinHuang8/DATT.
- DATT's public training example uses a mixed reference set and evaluates on
  randomized zigzag references, which supports training on multiple reference
  families rather than one Level3 path shape only:
  https://github.com/KevinHuang8/DATT.
- OmniDrones `Track` observes relative positions to future reference points,
  drone state, and optional time encoding; its reward includes position
  tracking, uprightness, spin, effort, and action smoothness:
  https://omnidrones.readthedocs.io/en/latest/tasks/single/Track.html.
- OmniDrones `FlyThrough` separates gate-plane/center reward from basic flight
  terms. Use that separation for our gate-aperture mini task:
  https://omnidrones.readthedocs.io/en/latest/tasks/single/FlyThrough.html.
- safe-control-gym provides clean quadrotor tracking configs with randomized
  initial state, explicit reference tracking tasks, constraints, and MSE-style
  metrics:
  https://github.com/learnsyslab/safe-control-gym/blob/main/examples/rl/config_overrides/quadrotor_3D/quadrotor_3D_track.yaml.
- Stable-Baselines3 documents PPO's clipping/advantage-normalization behavior
  and recommends trying frame/history stacking before recurrent PPO for many
  cases:
  https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html.
- Racing-specific results warn that a pure time-indexed trajectory interface can
  be brittle under mismatch. Keep the tracker feedback-driven and include
  margins, braking, and action smoothness instead of only replaying points:
  https://arxiv.org/abs/2310.10943.

## Observation Guidance

Prefer body-frame or local-frame features so the tracker learns a reusable
servo law:

- current reference error and several future reference-point errors;
- desired velocity or desired speed along the local segment;
- desired heading or yaw error;
- current velocity, angular velocity, attitude/up/heading features;
- previous action or short action history;
- reference phase or time encoding when switching points;
- local gate-aperture geometry only for gate-aperture tasks.

If using asymmetric PPO later, the critic may receive privileged exact state,
dynamics randomization values, or full reference state during training only.
The deployed actor must still use only deployed observations.

## Curriculum Guidance

Use this order unless a decision packet justifies a different one:

1. `hover`
2. `point_hold`
3. `point_reach`
4. `brake_to_point`
5. `line_tracking`
6. `heading_tracking`
7. `multi_point_reference`
8. `l_shape_tracking`
9. `curve_tracking`
10. `zigzag_or_lemniscate_tracking`
11. `gate_aperture_reference`
12. `planner_integration_smoke`

Start with fixed/easy references. Then randomize start state, endpoint, speed,
curvature, and point timing. Add disturbance, latency, and domain
randomization only after nominal tracking works.

## Reward Guidance

Keep tracker reward local and measurable:

- position error / cross-track error;
- final error near target;
- velocity or desired-speed error;
- heading/yaw error;
- terminal speed near target for braking tasks;
- phase completion or valid aperture crossing for gate mini tasks;
- action norm and action-delta smoothness;
- uprightness, spin/body-rate limits, and crash/timeout penalties.

Avoid full-race global progress reward during early tracker qualification. It
can hide the real failure mode: the policy may move forward without being able
to stop, align, or follow the reference precisely.

## Metrics And Gates

Every rung should report:

- mean/median/final position error;
- RMSE or MSE where available;
- cross-track error for path tasks;
- velocity error and terminal speed;
- overshoot distance;
- heading/yaw error;
- crash, timeout, and early-termination rate;
- action norm and action delta;
- finite observation/action checks;
- held-out seed/reference split;
- checkpoint path and W&B run URL.

For gate-aperture and planner smoke, add valid plane crossing, aperture margin,
post-gate recovery, first-gate progress, and gate-0 pass count.

Do not approve long planner-driven Level3 training until the tracker passes the
mini-task gates and strict planner smoke on unchanged `config/level3.toml`.

## PPO Hygiene

During training analysis, inspect PPO diagnostics alongside task metrics:

- approximate KL and clip fraction;
- entropy and action standard deviation;
- value loss / explained variance;
- reward scale relative to value clipping;
- rollout length and batch size;
- checkpoint milestone curve, not only the final checkpoint.

If the tracker is partially observable after history/future references are
included, then consider GRU. Do not make GRU the first fix for a tracker that
has not yet passed hover, point, line, and braking tasks.
