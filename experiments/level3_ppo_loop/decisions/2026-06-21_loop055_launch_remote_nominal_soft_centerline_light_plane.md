# Main-Agent Decision After Loop055

Date: 2026-06-21

## Decision

`launch_named_structural_lane`

## Latest Trial

Trial:

`level3_loop_055_v5_loop052_nominal_reward_ppo_update_pressure_20m`

Best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_055_v5_loop052_nominal_reward_ppo_update_pressure_20m/level3_loop_055_v5_loop052_nominal_reward_ppo_update_pressure_20m_step_010000000.ckpt`

Metrics:

- Success: `0.15`
- Mean successful time: `6.62s`
- Crash: `0.85`
- Mean gates: `1.05`
- Target met: `false`

Global best remains:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Global-best metrics:

- Success: `0.20`
- Mean successful time: `6.975s`
- Crash: `0.80`
- Mean gates: `1.40`

## Subagent Review Synthesis

`evaluator_metrics`:

- Do not continue loop055.
- Loop055 peaked at `0.15` success and regressed to `0.05` success by final.
- Global best remains loop052.

`wandb_ppo_diagnostics`:

- Do not continue the update-pressure lane.
- Higher `learning_rate=8e-5` and `update_epochs=6` raised training activity
  but did not convert into hard-eval progress.
- Gate/finish/plane-cross signals stayed flat while wrong-side rate rose.
- Recommended a named lane from loop052 focused on correct gate-plane
  conversion, with PPO pressure reverted.

`structure_research_synthesis`:

- Do not blindly continue v5 nominal or launch another unpacketized tweak.
- The failure looks like a pass-through/survival structural ceiling.
- If a new lane is launched, it must be explicitly packeted, bounded, and start
  from loop052.

## Rationale

Loop055 falsifies increased PPO update pressure from loop052. Loop053 already
tested same-lane maturation and loop054 already tested stronger gate pressure.
The next useful test is not more steps on loop055 and not another high-pressure
reward scale.

This decision launches a bounded, packeted structural reward-lane that is not a
repeat of older soft-centerline tests:

- Start from the current global best loop052 checkpoint, not the older loop020
  branch.
- Use loop052's lower remote nominal PPO and safety scale.
- Revert PPO pressure to nominal settings.
- Add only light centered plane/followthrough signals to test whether W&B
  gate-plane/correct-side conversion can improve without destabilizing the
  policy.

## Approved Next Lane

Name:

`v5_loop052_remote_nominal_soft_centerline_light_plane_20m`

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Training:

- `20M` steps
- `5M` checkpoint interval
- W&B enabled
- hard eval on unchanged `config/level3_dr.toml`

Structural change:

- `reward_structure=soft_centerline_followthrough`
- `gate_plane_bonus=16.0`
- `missed_gate_penalty=6.0`
- `gate_frame_pressure_coef=0.35`
- `wrong_side_penalty=12.0`

Everything else stays at the loop052 remote nominal scale, including v5
observation and nominal PPO settings.

## Stop/Continue Criteria

Continue only if the lane improves over loop052 or shows clear conversion:

- success `>0.20`; or
- success `0.20` with mean gates `>1.40`; or
- success `>=0.15`, mean gates `>=1.40`, crash `<=0.85`, and W&B
  gate-plane/finish signals improve.

Rollback or hold if:

- best success stays `<=0.15` with mean gates below `1.20`; or
- crash stays `>=0.85` and W&B gate/finish/plane-cross signals remain flat; or
- final regresses to `<=0.05` success.

