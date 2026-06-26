# V60 Reference Command No-Gate Reward Bounded Smoke

Date: 2026-06-26T21:15:09+02:00

Status: bounded smoke completed; pipeline clean; stage gate not unlocked.

## Purpose

This was a plumbing and semantics smoke for:

```text
v60_reference_command_tracker_no_gate_reward
```

It was not a learning-quality judgment. The run used only `4096` timesteps, so
the stage gate was not expected to pass.

## Train Smoke

Command summary:

```bash
pixi run -e gpu python lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  --config level3_tracker_free_space.toml \
  --task reference_command_no_gate_reward \
  --tracker-env-mode free_space \
  --observation-layout auto \
  --seed 26060 \
  --total-timesteps 4096 \
  --num-envs 16 \
  --num-steps 256 \
  --num-minibatches 4 \
  --update-epochs 4 \
  --checkpoint-interval 0 \
  --model-path lsy_drone_racing/control/checkpoints/v60_reference_command_no_gate_reward_smoke/v60_reference_command_no_gate_reward_smoke_final.ckpt \
  --wandb-enabled \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v60_reference_command_no_gate_reward_smoke_4096 \
  --wandb-run-id v60_reference_command_no_gate_reward_smoke_20260626 \
  --cuda
```

Result:

- Exit code: `0`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v60_reference_command_no_gate_reward_smoke_20260626`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/v60_reference_command_no_gate_reward_smoke/v60_reference_command_no_gate_reward_smoke_final.ckpt`
- `config/level3.toml`: unchanged.

Checkpoint metadata:

- `task`: `reference_command_no_gate_reward`
- `requested_task`: `reference_command_no_gate_reward`
- `observation_layout`: `level3_reference_tracker_command_v3`
- `obs_dim`: `56`
- `total_timesteps`: `4096`
- `num_envs`: `16`
- `num_steps`: `256`
- Gate/aperture reward coefficients forced to zero:
  `gate_center_coef`, `gate_x_progress_coef`, `gate_cross_bonus`,
  `gate_recover_bonus`, `gate_linger_penalty_coef`.

Note: W&B still has some `tracker/gate_*` diagnostic names from shared
evaluator code. They are diagnostics only here; the v60 reward coefficients are
zero and the actor observation is the clean `command_v3` layout.

## Evaluation Smoke

Evaluator command:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage reference_command_no_gate_reward \
  --checkpoint lsy_drone_racing/control/checkpoints/v60_reference_command_no_gate_reward_smoke/v60_reference_command_no_gate_reward_smoke_final.ckpt \
  --output /tmp/v60_reference_command_no_gate_reward_smoke_metrics.json \
  --episodes 20 \
  --seeds 101-120 \
  --max-episode-steps 500
```

Key metrics:

- `checkpoint_backed`: `true`
- `all_finite`: `true`
- `semantic_waypoint_type_count`: `4.0`
- `success_rate`: `0.0`
- `crash_rate`: `1.0`
- `mean_brake_hold_position_error_m`: `0.7372176051139832`
- `mean_slow_through_position_error_m`: `0.8282440900802612`
- `mean_brake_hold_speed_mps`: `0.17322863638401031`
- `p90_brake_hold_speed_mps`: `0.3071606755256653`
- `mean_slow_through_speed_mps`: `0.40083009004592896`
- `brake_hold_rush_count`: `0.0`
- `slow_through_stop_count`: `0.0`

## Gate Checker

Gate checker:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage reference_command_no_gate_reward \
  --metrics-json /tmp/v60_reference_command_no_gate_reward_smoke_metrics.json \
  --output /tmp/v60_reference_command_no_gate_reward_smoke_gate.json
```

Result:

- `passed`: `false`
- `next_stage_unlocked`: `null`

Passed smoke/plumbing checks:

- checkpoint-backed evaluation;
- finite observations/actions;
- all four command types covered;
- low-speed-through did not stop dead;
- brake/hold did not rush through by the explicit rush counter.

Failed learning-quality gates:

- `success_rate`: `0.0 < 0.8`
- `crash_rate`: `1.0 > 0.08`
- brake/hold and slow-through position errors are still too large;
- brake/hold speed is still slightly above the strict gate.

These failures are expected after `4096` timesteps and should not be interpreted
as evidence that v60 is a bad learning direction.

## Decision-Relevant Conclusion

The v60 support is smoke-clean:

```text
trainer -> W&B -> checkpoint metadata -> evaluator -> gate checker
```

all ran without semantic/plumbing failure. The next useful step is a bounded
stage-maturation chunk for the same stage, not planner-driven Level3 long
training and not a v59 local-safety extension.

Recommended next step:

```text
continue_same_stage_more_steps:
  run v60 reference_command_no_gate_reward maturation
  default budget: 8M timesteps
  vectorized rollout: 1024 envs x 32 steps
  checkpoint interval: 1M
  evaluate milestone checkpoints before judging the stage
```
