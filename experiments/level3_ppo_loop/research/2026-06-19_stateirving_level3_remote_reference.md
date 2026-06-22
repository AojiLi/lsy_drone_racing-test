# stateirving Level3 Remote Reference

Date: 2026-06-19

Source: https://github.com/stateirving/lsy_drone_racing
Fetched ref: `origin/main` at `58e8e1a` (`level3 finetuning notebook`)

## Relevant Remote Changes

- `480d743` introduced Level3 observation metadata and new Level3 observation support.
- `462e8fb` moved from the larger all-gates observation to a smaller local observation.
- Final remote Level3 controller default points to:
  `checkpoints/level3_localobs_relax/level3_localobs_relax_final.ckpt`.

The strongest remote branch is not the all-gates/v4 checkpoint. It is:

- Layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Checkpoint family: `level3_localobs_relax`
- Hidden dim: `256`
- Observation dim: `68`

The v5 observation contains:

- base drone state: z, body velocity, angular velocity, rotation matrix
- current target gate corners in body frame
- target gate known/visited flag
- nearest non-target gate corners in body frame
- nearest non-target gate known/visited flag
- nearest 2 obstacle features in heading frame: forward, left, xy distance, detected
- previous normalized action
- short local history with z, body velocity, angular velocity

## Remote Training Recipe

The remote notebook trains `level3_localobs_relax` on `level3_dr.toml` for about
300M steps with:

- `num_envs=1024`
- `num_steps=32`
- `hidden_dim=256`
- `learning_rate=3e-4`
- `ent_coef=0.02`
- `target_kl=0.03`

Reward numbers in the notebook:

- `progress_coef=0.0`
- `gate_stage_coef=15.0`
- `gate_axis_coef=15.0`
- `gate_bonus=120.0`
- `gate_back_bonus=20.0`
- `finish_bonus=160.0`
- `wrong_side_penalty=6.0`
- `crash_penalty=50.0`
- `obstacle_coef=5.0`
- `obstacle_margin=0.3`
- `timeout_penalty=80.0`
- `time_penalty=0.03`
- `act_coef=0.03`
- `d_act_th_coef=0.1`
- `d_act_xy_coef=0.1`
- `cmd_tilt_coef=1.0`
- `rpy_coef=1.0`
- `tilt_limit_deg=40.0`
- `tilt_excess_coef=15.0`

This is not pure reward-only evidence because the strongest checkpoint depends
on a different observation layout. However, the reward numbers are a useful
reward-only hypothesis candidate for the current original observation lane.

## Hard Eval Results

Evaluation command used current local hard-eval logic against the remote
worktree and `config/level3_dr.toml`, with `ppo_level3_inference`.

20-seed screen:

| Checkpoint | Layout | Success | Mean Gates | Mean Successful Time | Crash |
| --- | --- | ---: | ---: | ---: | ---: |
| `level3_localobs_relax:100M` | v5 local obstacle | 0.05 | 0.80 | 5.64s | 0.95 |
| `level3_localobs_relax:150M` | v5 local obstacle | 0.10 | 1.05 | 5.98s | 0.90 |
| `level3_localobs_relax:200M` | v5 local obstacle | 0.15 | 1.25 | 6.22s | 0.85 |
| `level3_localobs_relax:230M` | v5 local obstacle | 0.15 | 1.25 | 6.30s | 0.85 |
| `level3_localobs_relax:250M` | v5 local obstacle | 0.10 | 1.00 | 6.11s | 0.90 |
| `level3_localobs_relax:270M` | v5 local obstacle | 0.10 | 1.10 | 6.33s | 0.90 |
| `level3_localobs_relax:280M` | v5 local obstacle | 0.20 | 1.40 | 6.35s | 0.80 |
| `level3_localobs_relax:290M` | v5 local obstacle | 0.10 | 1.40 | 5.54s | 0.90 |

100-seed confirmation:

| Checkpoint | Layout | Success | Mean Gates | Mean Successful Time | Crash |
| --- | --- | ---: | ---: | ---: | ---: |
| `level3_localobs_relax:200M` | v5 local obstacle | 0.12 | 1.24 | 6.55s | 0.88 |
| `level3_localobs_relax:280M` | v5 local obstacle | 0.16 | 1.33 | 6.59s | 0.84 |

Negative controls:

| Checkpoint | Layout | 20-seed Success | Mean Gates | Comment |
| --- | --- | ---: | ---: | --- |
| `level3_newobs_relax:final` | all-gates/v4 | 0.00 | 0.65 | Supports rejecting v4/all-gates for now. |
| `level3_DR_initial:200M` | original `obstacle_heading_xy_v1` | 0.00 | 1.00 | More steps alone did not solve Level3. |

## Interpretation

The remote evidence supports three conclusions:

1. The deleted all-gates/v4 direction is not the promising remote result.
2. The promising result comes from a smaller local observation v5 plus a lower,
   smoother reward scale.
3. The remote result is better than the current local best in hard eval, but it
   is still far below the target of 60% success.

Current local best for comparison:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_016_loop010_step_curve_maturation_100m/level3_loop_016_loop010_step_curve_maturation_100m_step_055000000.ckpt`
- Success: `0.05`
- Mean gates: `0.95`
- Mean successful time: `6.10s`
- Crash: `0.95`

## Recommended Use

Do not merge the whole remote branch blindly. Split it into two lanes:

1. Reward-only lane, allowed under the current loop constraints:
   test the remote reward-number scale on the current original observation.
2. Structural observation lane, requires explicit user approval:
   implement and evaluate `level3_target_gate_nearest_gate_2obs_local_history_v5`
   as a separate Stage 2 observation packet.

Recommended immediate reward-only hypothesis:

- `gate_stage_coef=15.0`
- `gate_axis_coef=15.0`
- `gate_bonus=120.0`
- `gate_back_bonus=20.0`
- `finish_bonus=160.0`
- `wrong_side_penalty=6.0`
- `crash_penalty=50.0`
- `obstacle_coef=5.0`
- `obstacle_margin=0.3`
- `timeout_penalty=80.0`
- `time_penalty=0.03`
- `act_coef=0.03`
- `d_act_th_coef=0.1`
- `d_act_xy_coef=0.1`
- `cmd_tilt_coef=1.0`
- `rpy_coef=1.0`
- `tilt_limit_deg=40.0`
- `tilt_excess_coef=15.0`

Keep disabled channels disabled in the reward-only lane:

- `progress_coef=0.0`
- `near_gate_coef=0.0`
- `gate_plane_bonus=0.0`
- `missed_gate_penalty=0.0`
- `obstacle_clearance_coef=0.0`

