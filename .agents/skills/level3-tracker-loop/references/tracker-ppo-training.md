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

For planner-driven Level3, the reference should include command intent, not
only a single target point. The user has rejected the earlier v58 direction
when it is framed as gate/aperture semantics. Treat the next durable interface
as v60 no-gate command tracking:

```text
current_reference_point
next_point
lookahead_point
desired_velocity
desired_speed
desired_heading
generic pass-through / hold-brake / low-speed-through / speed-recovery intent
last_action / short history
```

The main instruction should come from the trajectory horizon, speed/velocity,
and heading. Labels or masks are auxiliary hints, not a replacement for
concrete flight commands. For example, a hold/brake command should look like a
nearly stationary short horizon with low desired speed and alignment heading;
a low-speed-through command should look like future points moving through a
constrained segment with low but nonzero speed.

The v60 reference generator should present dense rolling mini-trajectories, not
a few sparse waypoints. For moving commands, set `desired_velocity` along the
short visible horizon (`current -> lookahead`) so the policy learns to follow
the trajectory segment. For hold/brake, keep `current`, `next`, and `lookahead`
near the same brake point and make `desired_velocity` near zero. Point spacing
should be consistent with the commanded speed and simulator `dt`; for example,
at `0.30m/s` and `50Hz`, the visible reference should advance only a few
millimeters per simulator step, with `next` and `lookahead` only modestly ahead.
Randomize direction, length, altitude, curvature, speed, phase duration,
braking distance, slow-through distance, and recovery angle so the bottom
tracker learns generic command following rather than a single fixed route.
Keep the sequence shaped like the future conservative Level3 planner: cruise,
slowdown/hold, low-speed-through, and smooth speed recovery.

Brake intent should start before the hold point. Avoid an abrupt transition
from high-speed `pass_through` to zero-velocity `hold_or_brake`; instead, the
approach command should taper speed and reference spacing over a deceleration
zone. A good default for v60 is to cruise around `0.55-0.78m/s`, then ramp down
to roughly `0.15-0.24m/s` before entering the hold/brake horizon. This gives the
policy a learnable "prepare to stop" command rather than requiring it to cancel
inertia instantly at the phase boundary.

Recommended generic command intents:

- `pass_through`: pass smoothly through the point at the commanded speed;
- `hold_or_brake`: slow to about `0.0-0.1m/s`, reduce overshoot, and stabilize;
- `low_speed_through`: continue at about `0.25-0.35m/s` without stopping dead;
- `recover_speed`: restore speed gradually after the constrained segment.

If the actor cannot observe the future reference horizon, desired speed, and
heading clearly enough, it may treat every waypoint as a pass-through point.
That matches the v57a failure pattern: references became continuous, but actual
phase4 speed stayed too high and contacts persisted. A label alone is
not sufficient evidence that the command is trackable.

Do not encode gate pass, aperture crossing, finish, race progress, or stage
progress as tracker actor inputs for v60. Those are planner-integration or final
evaluation concepts, not bottom-servo training concepts.

For the clean v60 baseline, also remove gate, obstacle, and planner phase
features from the actor input. Use `level3_reference_tracker_command_v3`: self
state, reference horizon, desired velocity/speed/heading, generic command masks,
last action, and history only. Obstacle/frame information belongs to a later
local-safety-reflex lane if evidence requires it, not to the clean baseline.

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
11. `reference_command_no_gate_reward`
12. `planner_integration_smoke`

`gate_aperture_reference` is now optional diagnostic only. Use it when a
planner-generated pre-gate/aperture/post-gate reference appears untrackable and
needs isolation, but do not make it a mandatory reward-shaped training stage.
The old `semantic_planner_reference` v58 stage is now held. Replace it with a
v60 no-gate command stage whose command intent is expressed by future reference
points, desired speed/velocity, desired heading, and optional generic masks for
pass-through, hold/brake, low-speed-through, and speed recovery. The bottom
tracker should not receive gate/aperture pass reward while learning this stage.

Start with fixed/easy references. Then randomize start state, endpoint, speed,
curvature, and point timing. Add disturbance, latency, and domain
randomization only after nominal tracking works.

## Training Budget Guidance

Tiny runs are plumbing checks, not learning evidence. The local tracker trainer
defaults to `--total-timesteps 4096`, which is useful for smoke tests only.

Source-backed scale:

- safe-control-gym quadrotor PPO configs use about `1M` environment steps as a
  small-task/default floor.
- DATT-style quadrotor trajectory tracking is in the `15M-25M` step range.
- OmniDrones task examples report `5M` frames for FlyThrough and `20M` frames
  for Track with large parallel simulation.
- agile quadrotor PPO tracker/controller comparisons report around `50M`
  environment interactions.
- full drone racing, obstacle-rich generalization, or vision-based racing often
  uses `100M+` interactions.

For this repo, use explicit stage budgets from
`experiments/level3_ppo_loop/tracker_qualification_gates.json`. Treat the
default stage budget as the first real maturation chunk, not a failure ceiling.
If milestone checkpoints are still improving after the default chunk, prefer a
same-stage extension decision before changing reward, observation, network
structure, or planner logic.

Do not run tracker learning chunks through the old single-env PPO loop. It is
too slow and changes the meaning of "1M steps" into a long wall-clock run. Use
vectorized PPO rollout geometry:

- default: `1024 envs x 32 steps = 32768 samples/update`, matching earlier PPO
  training precedent in this repo;
- longer-horizon alternative: `256 envs x 128 steps = 32768 samples/update`,
  if a decision packet finds the short rollout horizon is hurting a tracker
  stage.

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

For command-intent training, split reward by intended trajectory behavior:

- `pass_through`: reward smooth path following and speed tracking, not stopping;
- `hold_or_brake`: reward low terminal speed, low overshoot, and short dwell
  stability near the target;
- `low_speed_through`: reward motion at the commanded low speed, penalizing both
  rushing through and stopping dead;
- `recover_speed`: reward gradual speed restoration and smooth action changes.

For the clean v60 baseline, route `reference_command_no_gate_reward` through
`ReferenceCommandReward`, not the legacy gate-capable `ReferenceTrackerReward`.
The v60 reward formula and diagnostics should contain no gate-center,
gate-progress, gate-cross, gate-recover, gate-linger, obstacle, finish,
race-progress, or stage-progress terms. Keep the legacy reward path only for old
v1/v2 compatibility and gate-aperture diagnostics.

Do not leave v60 as a pure current-point chase. The input already contains
`current_point`, `next_point`, `lookahead_point`, desired velocity/speed, and
desired heading. The reward should use that horizon directly:

- moving commands: penalize cross-track error to the short horizon, penalize
  along-track speed mismatch and reverse motion, and reward progress along the
  horizon;
- `hold_or_brake`: keep point accuracy and low speed dominant, and penalize
  overshoot past the commanded stop point along the horizon direction;
- diagnostics should expose command-position error, command-velocity error,
  cross-track error, along speed, reverse speed, brake overshoot, and command
  progress for W&B analysis.

These are still generic tracker rewards. They must not depend on gate,
aperture, obstacle, planner phase, race progress, or target-gate transition
state.

Avoid full-race global progress reward during early tracker qualification. It
can hide the real failure mode: the policy may move forward without being able
to stop, align, or follow the reference precisely.

Do not reward the presence of a label by itself. Reward the measurable behavior
implied by the concrete command: position/horizon tracking, desired-speed
tracking, heading tracking, low overshoot, and smooth actions.

Do not add gate-pass bonus, aperture-crossing bonus, finish bonus, race-progress
bonus, stage-progress bonus, or target-gate transition reward to the bottom
tracker. If a future experiment needs to evaluate gate passage, keep it in
planner integration smoke on unchanged `config/level3.toml`, not in tracker
training reward.

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

For optional gate-aperture diagnostics and required planner smoke, add valid
plane crossing, aperture margin, post-gate recovery, first-gate progress, and
gate-0 pass count.

For v60 no-gate command references, add per-command metrics:

- error and speed error by command type;
- hold/brake terminal speed;
- low-speed-through speed in the constrained segment;
- overshoot after hold/brake targets;
- dwell stability for hold targets;
- wrong behavior counts, such as rushing through a brake point or stopping at a
  low-speed-through point.

Do not approve long planner-driven Level3 training until the tracker passes the
required free-space tracker gates through `zigzag_or_lemniscate_tracking` and
strict planner smoke on unchanged `config/level3.toml`.

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
