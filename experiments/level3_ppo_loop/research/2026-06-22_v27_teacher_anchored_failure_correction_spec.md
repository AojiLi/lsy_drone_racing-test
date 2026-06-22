# V27 Teacher-Anchored Failure-Correction Specification

Status: specification only. Do not launch training until the user approves a
v27 implementation packet and the state hold is explicitly overridden.

## Objective

Address successful-behavior forgetting on Level3 without changing
`config/level3_dr.toml`.

The experiment should retain behavior from a validated teacher checkpoint while
training targeted failure-correction cases. After unseen validation
re-evaluation, the current teacher/action anchor is loop052 final.

## Fixed Components

- hard-eval config: unchanged `config/level3_dr.toml`
- observation layout: `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- controller/inference path: `ppo_level3_inference`
- PPO family: existing PPO implementation
- initial training scale: 5M screens, not long maturation
- checkpoint interval: 1M

Do not change observation, hidden width, GRU, PPO optimizer parameters, or
Level3 track geometry in the first v27 screen.

## Data

Use four disjoint seed roles:

- `dev_seen`: seeds 1-20, historical compatibility only
- `validation_unseen`: seeds 101-200, checkpoint promotion
- `final_locked`: seeds 1001-1200, final certification only
- `train_pool`: all other training/curriculum/replay seeds

Do not put `dev_seen`, `validation_unseen`, or `final_locked` seeds into a
training replay profile.

Collect retention trajectories from successful teacher episodes in `train_pool`.
Store:

- observation
- teacher action mean
- teacher action log standard deviation
- target gate index
- gate/obstacle clearance diagnostics
- success time

Collect failure-correction trajectories by failure geometry class, not exact
hard-eval seed id:

- `gate_side_frame`
- `near_gate_obstacle`
- `pre_plane_obstacle`

## Loss

Add a teacher KL only on retention states:

`L_total = L_PPO + beta * KL(pi_teacher || pi_student)`

The KL should constrain drift on known successful behavior while still allowing
the student to improve failure-correction states.

## Minimal Screen

Run only three 5M screens:

- `v27-control`: beta = 0.00
- `v27-light`: beta = 0.03
- `v27-medium`: beta = 0.10

Every 1M checkpoint:

1. evaluate `dev_seen`
2. promote only promising checkpoints to `validation_unseen`
3. do not inspect `final_locked`

## Promotion Gate

A v27 checkpoint may promote only if it satisfies at least one reliability
improvement and preserves teacher behavior:

- validation success improves over anchor by at least 10 percentage points, or
- validation crash drops by at least 15 percentage points and mean gates rises
  meaningfully

and:

- teacher successful-behavior retention >= 80%
- success does not drop more than 5 percentage points for a speed gain

If no beta passes the gate, stop and write a hold decision rather than maturing
to 60M.
