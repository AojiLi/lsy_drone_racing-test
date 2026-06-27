# v62c Milestone Value/Velocity Review

Date: 2026-06-27

## Purpose

Evaluate every saved `v62c_tanh_squashed_gaussian_10m` milestone checkpoint
from `1M` through `9M`, plus final, and answer:

```text
Which checkpoint is best?
When did command velocity tracking start getting worse?
```

This is a tracker free-space command-following review, not a Level3 hard eval.
It does not approve planner integration or 60M+ maturation.

## Eval Protocol

Generated metrics:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62c_milestone_value_velocity_review.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62c_milestone_value_velocity_review.csv
```

Protocol:

| Field | Value |
|---|---:|
| config | `level3_tracker_free_space.toml` |
| seed | `26310` |
| num envs | `1024` |
| num steps | `32` |
| eval rollouts | `16` |
| action distribution | `tanh_squashed_gaussian` |
| initial log std | `-2.0` |

Each checkpoint was evaluated from a fresh reset with the same raw-observation
seed, `eval_plan_key`, and `eval_key` protocol used by the v62 lane. The
generated JSON/CSV artifacts remain ignored by git.

An attempted W&B history scan for full value/advantage curves was interrupted
after it did not return in a bounded window. This packet uses checkpoint eval
plus the already-recorded v62c 10M final training-batch diagnostics.

## Results

| checkpoint | step | reward | pos err | cross-track | vel err | done | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| initial | 0 | -6.4882 | 1.0461 | 0.6477 | 0.6465 | 0.00557 | -10.0926 |
| 1M | 1,048,576 | -5.3825 | 0.6185 | 0.5064 | 0.8826 | 0.00586 | -8.0997 |
| 2M | 2,097,152 | -5.2551 | 0.5689 | 0.4497 | 0.9279 | 0.00586 | -7.8220 |
| 3M | 3,145,728 | -6.0378 | 0.5983 | 0.4862 | 1.0272 | 0.00781 | -8.8124 |
| 4M | 4,194,304 | -5.2135 | 0.5842 | 0.4667 | 0.8732 | 0.00586 | -7.7956 |
| 5M | 5,242,880 | -4.9391 | 0.6460 | 0.5272 | 0.8203 | 0.00412 | -7.6783 |
| 6M | 6,291,456 | -5.4806 | 0.6336 | 0.5235 | 0.8980 | 0.00586 | -8.2653 |
| 7M | 7,340,032 | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | -7.5365 |
| 8M | 8,388,608 | -5.4516 | 0.6395 | 0.5294 | 0.8798 | 0.00586 | -8.2433 |
| 9M | 9,437,184 | -5.3189 | 0.6108 | 0.5014 | 0.8696 | 0.00586 | -8.0034 |
| final | 10,027,008 | -5.6864 | 0.6899 | 0.5718 | 0.8915 | 0.00586 | -8.6510 |

Balanced score is a review-only ranking heuristic:

```text
reward
- 2.0 * position_error
- 1.5 * cross_track_error
- 0.75 * velocity_error
- 10.0 * done_mean
- 2.0 * action_delta_penalty
```

## Best Checkpoint

Best overall checkpoint:

```text
7M
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

It is best by:

- reward mean: `-4.8459`;
- balanced score: `-7.5365`;
- command velocity error among trained checkpoints: `0.7397`;
- done mean among trained checkpoints: `0.00391`.

Best position and cross-track checkpoint:

```text
2M
```

`2M` has the best position error `0.5689` and cross-track error `0.4497`, but
its velocity error is poor at `0.9279`, so it is not the best deployment or
resume candidate.

Final is not best. It is worse than `7M` on reward, position error, cross-track
error, velocity error, done mean, and balanced score.

## Velocity Degradation

There are two useful answers:

1. Compared with the untrained initial policy under the same 16-rollout eval
   protocol, velocity error is already worse at `1M`:

   ```text
   initial velocity error = 0.6465
   1M velocity error      = 0.8826
   ```

   No later checkpoint gets back below the initial velocity error. This means
   the current reward/training setup improves geometry tracking while paying for
   it with worse speed tracking almost immediately.

2. Compared within the trained milestone curve, velocity is least bad at `7M`
   and starts worsening again at `8M`:

   ```text
   7M velocity error = 0.7397
   8M velocity error = 0.8798
   9M velocity error = 0.8696
   final velocity error = 0.8915
   ```

   This supports selecting `7M` rather than final if a future experiment needs a
   v62c checkpoint seed.

## Interpretation

v62c did learn useful spatial tracking:

```text
initial position error: 1.0461
2M position error:      0.5689
7M position error:      0.6573

initial cross-track:    0.6477
2M cross-track:         0.4497
7M cross-track:         0.5214
```

But it did not learn clean velocity tracking. The policy appears to trade speed
matching for getting closer to the reference path. That is risky for the
planner/tracker architecture because the Level3 planner depends on the bottom
tracker obeying slowdown, hold, low-speed-through, and recovery commands.

The final checkpoint is an example of late training drift, not maturation:
relative to `7M`, final has worse reward, worse position error, worse
cross-track error, worse velocity error, and worse done rate.

## Conclusion

Do not launch 60M+ v62c maturation from this configuration, and do not resume
from final as the default checkpoint.

Use `7M` as the best diagnostic checkpoint from this run. It is not a passed
tracker policy, because velocity error remains worse than the initial policy.

The next useful work is a value/velocity stabilization support pass before
another long chunk:

- preserve the v62c tanh-squashed action path;
- keep `level3_reference_tracker_command_v3`;
- keep no-gate/no-aperture/no-race reward boundaries;
- add or test value/return normalization or critic target scaling;
- strengthen diagnostics and/or command velocity weighting only in generic
  trajectory-command terms;
- run a bounded follow-up from the selected checkpoint only after builder/checker
  support passes.
