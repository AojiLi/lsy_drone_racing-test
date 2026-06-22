# Launch V28 Success24 Retention + Bounds Replay 5M

Decision: launch_named_structural_lane

Approved structural hypothesis:

`v28_success24_retention_bounds_replay_5m`

## Why This Lane

Loop087 proved that the real teacher-retention KL is wired and numerically
healthy, but beta=0.10 with the original 8-episode retention dataset did not
beat the loop052 validation anchor.

The next useful experiment is not a larger beta or a long maturation of the
same narrow data. It is a data-correction lane:

- preserve loop052 teacher success behavior using the larger success24
  train_pool retention dataset;
- start from loop087 final, which already learned the v27 KL constraint;
- mix a small amount of train_pool bounds-or-ground failure replay into
  training;
- keep final scoring on unchanged `config/level3_dr.toml`.

## Evidence

Current validation anchor, loop052 final:

- success rate: 0.20
- crash rate: 0.80
- mean gates: 1.47
- mean successful time: 6.858s

Loop087 beta=0.10 final:

- success rate: 0.17
- crash rate: 0.83
- mean gates: 1.50
- mean successful time: 6.991s
- retention batch size: 512
- teacher agreement tail: about 0.836

Success24 retention audit:

- dataset:
  `experiments/level3_ppo_loop/retention_datasets/v27_loop052_train_pool_success24_v5_teacher_v8_student.npz`
- samples: 8246
- teacher-success train_pool episodes: 24
- excluded seed overlap: none

Failure-correction probe and dataset:

- probe source:
  `experiments/level3_ppo_loop/analysis/2026-06-22_v28_train_pool_loop087_failure_probe_summary.csv`
- dataset:
  `experiments/level3_ppo_loop/failure_datasets/v28_loop087_train_pool_selected_bounds_failure_trajectories.npz`
- recorded samples: 5368
- recorded failure episodes: 29
- endpoint class: `bounds_or_ground`
- selected seeds: train_pool only, no dev, validation, or final_locked seeds
- failures by target gate: gate0=6, gate1=8, gate2=11, gate3=4

## Approved Training Shape

- hard eval config: unchanged `config/level3_dr.toml`
- training config: `level3_dr.toml`
- observation layout: `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- initial checkpoint: loop087 final
- teacher checkpoint: loop052 final
- teacher KL beta: 0.10
- retention dataset: success24 train_pool dataset
- track generator profile: `v28_train_pool_bounds_failure_replay`
- replay probability: 0.20
- training horizon: 5M
- checkpoint interval: 1M
- eval protocol: dev-to-validation milestone evaluation
- W&B project: `ADR-PPO-Racing-Level3`

## Boundaries

Do not:

- modify `config/level3_dr.toml` track geometry, gates, obstacles, or
  randomization;
- use final_locked seeds;
- continue beta=0 or beta=0.03;
- increase beta beyond 0.10 in this lane;
- launch more than one bounded train/evaluate chunk before analysis;
- accept W&B reward as the target without hard-eval conversion.

## Post-Run Requirement

After the 5M chunk:

1. run `scripts/analyze_level3_ppo_trial.py` with online W&B;
2. use exactly three reviews: evaluator metrics, W&B/PPO diagnostics, and
   structure/research synthesis;
3. write a main-agent decision packet before any next training chunk;
4. compare against loop052 final on validation success, crash, mean gates, and
   mean successful time.

Promotion signal:

- validation success at or above 0.20 with improved crash or mean gates, or
- clear nonzero improvement in gate progress without destabilizing retention.

Failure signal:

- success remains below loop052 while crash remains above 0.80;
- retention metrics remain healthy but do not convert to hard eval;
- replay overfits train_pool failure geometry without validation progress.
