# Loop065 Synthesis: Directional Pass Conversion Guard

## Context

Loop065 tested:

`v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety`

It kept the loop052 checkpoint, v5 local-obstacle observation, 2x256 Tanh MLP,
constant `learning_rate=5e-5`, `anneal_lr=False`, and nominal safety/control
numbers. It increased raw gate-acquisition rewards:

- `gate_stage_coef=13`
- `gate_axis_coef=24`
- `gate_front_bonus=5`
- `gate_bonus=200`
- `gate_back_bonus=35`
- `finish_bonus=175`
- `time_penalty=0.02`

Hard eval remained on unchanged `config/level3_dr.toml`.

## Evidence

Loop065 milestone hard eval:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| 5M | 0.05 | 0.80 | 0.95 | 5.54s |
| 10M | 0.10 | 1.05 | 0.90 | 7.06s |
| 15M | 0.10 | 1.05 | 0.90 | 6.58s |
| final | 0.15 | 1.25 | 0.85 | 6.39s |

Global best remains loop052:

- success rate: 0.20
- mean gates: 1.40
- mean successful time: 6.975s
- crash rate: 0.80

W&B/PPO diagnostics:

- Constant learning rate was active at `5e-5`.
- PPO update pressure existed and did not explode:
  - tail `approx_kl` around `0.0046`;
  - tail `clipfrac` around `0.0067`;
  - entropy remained high.
- Race conversion remained weak:
  - `passed_gate_rate` flat;
  - `finished_rate` flat;
  - `gate_plane_cross_rate` flat.
- v13 worsened control/safety versus loop052:
  - final `cmd_tilt_over_limit_frac=0.431`;
  - final `mean_action_delta_l2=0.324`;
  - crash remained 0.85.

## Interpretation

The narrow v13 hypothesis is rejected. Increasing raw gate pressure did not
produce stable correct-side pass conversion. The behavior looks closer to
"approach pressure without reliable directional crossing" than to a training
horizon problem.

This does not reject the v5 observation, 2x256 MLP, or constant learning rate.
It rejects continuing the same reward-number mix to 60M/90M without a change in
pass-conversion incentives.

## Next Hypothesis

Use a bounded directional pass-conversion reward screen:

`v14_mlp_loop052_constant_lr_directional_pass_conversion_guard`

Keep fixed:

- loop052 final initial checkpoint;
- unchanged `config/level3_dr.toml` hard eval;
- v5 local-obstacle observation;
- 2x256 Tanh MLP Actor/Critic;
- constant `learning_rate=5e-5`, `anneal_lr=False`;
- `legacy_staged` reward structure;
- loop052 nominal safety/control numbers;
- 20M screen with 5M checkpoint interval.

Change the reward numbers:

- `gate_stage_coef=12`
- `gate_axis_coef=18`
- `gate_bonus=150`
- `gate_front_bonus=14`
- `gate_back_bonus=55`
- `finish_bonus=220`
- `wrong_side_penalty=14`
- `time_penalty=0.0`

The hypothesis is that reduced raw gate pressure plus stronger directional
front/back and completion rewards should improve correct-side pass conversion
without further increasing crash-heavy approach behavior.

## Promotion And Rejection Rules

Promote toward 60M if any milestone checkpoint has:

- `success_rate > 0.20`, or
- `mean_gates > 1.45`, or
- `success_rate == 0.20` with `mean_gates > 1.40` and `crash_rate <= 0.80`,
  plus improving W&B pass/finish/plane-cross conversion.

Reject if all milestones have:

- `success_rate <= 0.15`, or
- `mean_gates < 1.30`, or
- `crash_rate >= 0.85` with flat pass/finish/plane-cross conversion.

Also reject if command tilt remains close to or worse than v13 final
`cmd_tilt_over_limit_frac=0.431`.
