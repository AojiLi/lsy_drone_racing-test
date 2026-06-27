# v62d_008 Hypothesis

Date: 2026-06-27

## Candidate

```text
v62d_008_velocity_contrast_constant_speed_generator
```

Family:

```text
C_generator_velocity_distribution
```

## Hypothesis

v62d_007 showed that a blunt reward-coefficient combination is not enough.
`speed_bin_balanced` improves spatial tracking, but velocity obedience remains
weak and late training still drifts.

The next single knob should change the generator distribution rather than add
another velocity reward number:

```text
command_generator_profile=velocity_contrast_constant_speed
```

The profile should over-sample:

```text
longer constant-speed windows
paired low/medium/high desired-speed variants on similar geometry
longer desired-velocity-consistent straight and gently curved segments
brake-ramp windows that taper speed before hold
low-speed-through windows that keep nonzero speed
recover windows that ramp speed smoothly
```

The goal is to make the same geometry appear with different desired speeds so
the actor cannot solve the task only by tracking position. It must learn that
`desired_velocity`, `desired_speed`, and the horizon spacing control how fast to
move.

## Guardrails

Keep:

```text
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
train_from_scratch=true
num_envs=1024
num_steps=32
num_minibatches=4
update_epochs=1
value_target_scale=1.0
command_vel_error_coef=default
```

Do not add:

```text
gate/aperture/race/finish/stage rewards
gate/obstacle/planner-phase actor inputs
Level3 track config changes
planner action output
```

## Required Support Before 30M

This candidate changes generator semantics, so builder/checker support is
required before full training.

Builder should implement the smallest generator-profile change in the existing
v60/v62 command-generator path. Checker must verify:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
COMMAND_GENERATOR_PROFILES includes velocity_contrast_constant_speed
checkpoint metadata records command_generator_profile=velocity_contrast_constant_speed
observation_layout remains level3_reference_tracker_command_v3
action_distribution remains tanh_squashed_gaussian
reward_coefficients remain default / no command_vel_error_coef override
no gate/aperture/obstacle/race/finish/stage reward is introduced
support smoke metrics are finite
action/logprob audit remains ok
```

## Support Smoke Draft

After builder/checker implementation, run a bounded support smoke:

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_support \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_008_velocity_contrast_constant_speed_support \
  --config level3_tracker_free_space.toml \
  --seed 26480 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 131072 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_support/v62d_008_velocity_contrast_constant_speed_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_support_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_constant_speed \
  --value-target-scale 1.0 \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_008_velocity_contrast_constant_speed_support \
  --wandb-run-id v62d_008_velocity_contrast_constant_speed_support_20260627 \
  --jax-device gpu
```

Do not launch 30M until support and checker pass.
