# v60 Command-Trajectory Smoke Decision

Date: 2026-06-26

## Decision

`continue_same_hypothesis`

The bounded v60 command-trajectory reward smoke is clean. Continue to an
explicit 8M maturation run for `reference_command_no_gate_reward`.

## Evidence

Smoke command completed and saved:

```text
lsy_drone_racing/control/checkpoints/v60_reference_command_trajectory_reward_smoke/v60_reference_command_trajectory_reward_smoke_final.ckpt
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v60_reference_command_trajectory_reward_smoke_20260626
```

Metadata confirms:

- `task = reference_command_no_gate_reward`
- `observation_layout = level3_reference_tracker_command_v3`
- `obs_dim = 56`
- `reward_model = reference_command_reward`
- all gate / obstacle / gate-cross coefficients are `0.0`
- new command-trajectory coefficients are present

Stage eval confirms:

- checkpoint backed: `true`
- all finite: `true`
- semantic waypoint type count: `4.0`

The stage gate did not pass:

- success rate: `0.0`
- crash rate: `1.0`
- mean brake/hold position error: `0.6842m`
- mean slow-through position error: `0.6464m`

This is expected for a 4096-step smoke and is not a reason to change reward,
input, PPO architecture, or curriculum.

## Guardrails

- `config/level3.toml` remains unchanged.
- Do not promote to planner integration.
- Do not change v60 observation layout.
- Do not add gate, aperture, obstacle, finish, race-progress, stage-progress, or
  target-gate transition rewards.
- Do not judge learning from this smoke.

## Approved Next Run

Run v60 maturation:

```bash
pixi run -e gpu python lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  --config level3_tracker_free_space.toml \
  --task reference_command_no_gate_reward \
  --tracker-env-mode free_space \
  --observation-layout auto \
  --seed 26066 \
  --total-timesteps 8000000 \
  --num-envs 1024 \
  --num-steps 32 \
  --num-minibatches 32 \
  --update-epochs 4 \
  --checkpoint-interval 1000000 \
  --model-path lsy_drone_racing/control/checkpoints/v60_reference_command_trajectory_reward_8m/v60_reference_command_trajectory_reward_8m_final.ckpt \
  --wandb-enabled \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v60_reference_command_trajectory_reward_8m \
  --wandb-run-id v60_reference_command_trajectory_reward_8m_20260626 \
  --wandb-mode online \
  --jax-device gpu \
  --cuda
```

After the run, evaluate all milestone checkpoints before deciding whether the
stage is passed, undertrained, or needs another structural/reward change.
