# Loop064 Synthesis: Gate-Acquisition Reward Numbers After Constant-LR Screen

## Context

Loop064 tested `v12_mlp_loop052_constant_lr_nominal_reward`:

- Initial checkpoint: loop052 final, the current global best.
- Observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Policy: existing 2x256 Tanh MLP Actor/Critic.
- Training change: `anneal_lr=False`, constant `learning_rate=5e-5`.
- Reward numbers: loop052 nominal reward scale.
- Hard eval: unchanged `config/level3_dr.toml`.

The purpose was to isolate whether the previous MLP/v5 fine-tuning runs were
limited by learning-rate annealing rather than reward or observation design.

## Evidence

Loop064 confirmed that constant learning rate was active:

- W&B summary recorded `charts/learning_rate=5e-05`.
- PPO diagnostics had nonzero update pressure:
  - tail `approx_kl` around `0.00436`;
  - tail `clipfrac` around `0.01235`;
  - entropy remained high rather than collapsing.

But hard eval did not beat loop052:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| 5M | 0.15 | 1.40 | 0.85 | 7.93s |
| 10M | 0.15 | 1.15 | 0.85 | 6.46s |
| 15M | 0.05 | 1.05 | 0.95 | 6.38s |
| final | 0.10 | 1.05 | 0.90 | 6.38s |

Global best remains loop052:

- success rate: 0.20
- mean gates: 1.40
- mean successful time: 6.975s
- crash rate: 0.80

W&B race metrics also did not show useful conversion:

- `race/passed_gate_rate` stayed nearly flat;
- `race/finished_rate` remained near zero;
- train reward moved down rather than converting into evaluator progress.

## Interpretation

The narrow v12 hypothesis is rejected: constant learning rate with nominal
loop052 rewards is not enough to improve the Level3 hard evaluator.

This does not reject the v5 observation, the 2x256 MLP, or constant learning
rate as a supporting training number. The useful finding is that PPO updates
are now happening, but the reward scale still does not push enough gate
acquisition and pass-completion behavior.

## Next Hypothesis

Use a bounded gate-acquisition reward-number screen:

`v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety`

Keep fixed:

- loop052 final initial checkpoint;
- v5 local-obstacle observation;
- 2x256 Tanh MLP Actor/Critic;
- constant `learning_rate=5e-5` with `anneal_lr=False`;
- loop052 nominal safety/control numbers;
- hard eval on unchanged `config/level3_dr.toml`.

Change only the gate-acquisition reward numbers:

- `gate_stage_coef=13`
- `gate_axis_coef=24`
- `gate_front_bonus=5`
- `gate_bonus=200`
- `gate_back_bonus=35`
- `finish_bonus=175`
- `time_penalty=0.02`

Run as a 20M screen with 5M milestone checkpoints.

## Promotion And Rejection Rules

Promote toward 60M/90M if any milestone checkpoint has:

- `success_rate > 0.20`, or
- `mean_gates > 1.45`, or
- `success_rate == 0.20` with better gate/finish conversion and crash no worse
  than 0.80.

Reject if all milestone checkpoints have:

- `success_rate <= 0.15`, or
- `mean_gates <= 1.20`, or
- `crash_rate >= 0.85` with flat W&B `passed_gate_rate`, `finished_rate`, and
  `gate_plane_cross_rate`.

Do not accept train reward alone as success.
