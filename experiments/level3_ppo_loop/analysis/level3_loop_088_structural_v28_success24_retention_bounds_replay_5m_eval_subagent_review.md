# Loop088 Evaluator Metrics Review

Verdict: `not_target_met`, but loop088 is a useful near-anchor improvement over
loop087. The 4M checkpoint is the only candidate worth carrying forward; the
final checkpoint regressed. Do not accept this as solved: success is 19%, far
below the >=60% target, despite successful episodes being fast enough.

| Checkpoint | Success | Crash | Timeout | Mean gates | Mean success time |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop052 anchor | 20% | 80% | 0% | 1.47 | 6.858s |
| loop087 final | 17% | 83% | 0% | 1.50 | 6.991s |
| loop088 4M best | 19% | 81% | 0% | 1.57 | 6.846s |
| loop088 final | 17% | 83% | 0% | 1.42 | 6.752s |

Loop088 4M improves over loop087 by +2pp success, -2pp crash, +0.07 mean
gates, and -0.144s mean successful time. Against loop052, it is still -1pp
success and +1pp crash, though it has better mean gates and slightly faster
successful runs.

Key evaluator metrics:

- best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_step_004000000.ckpt`
- validation split: `validation_unseen`, 100 episodes, hard eval on unchanged
  `config/level3_dr.toml`
- success CI95: 0.125 to 0.278
- median success time: 6.76s; p90 success time: 8.136s
- tilt: mean max 28.68deg, worst 62.39deg, tilt-over-limit fraction 0.026
- command tilt-over-limit fraction is high at 0.283, worse than loop087 final
  at about 0.250

Failure taxonomy:

- loop088 4M failures: 81 `bounds_or_ground`, 19 success, 0 timeout
- failure by target gate: gate0 33, gate1 20, gate2 23, gate3 5
- still primarily gate acquisition/conversion failure
- loop088 reduced loop087 gate0 failures from 38 to 33, but shifted many
  failures into gate1/gate2 rather than converting them to finishes
- success seed churn is real: versus loop052, loop088 keeps 11 anchor
  successes, gains 8 new successes, and loses 9 anchor successes

Recommended next action:

Choose `change_reward_or_training_numbers`, not acceptance and not unchanged
continuation. Use loop088 4M, not final, as the candidate parent if continuing
this lane. Increase gate acquisition/conversion pressure and keep milestone
hard eval on `config/level3_dr.toml`. Do not use `final_locked` seeds.
