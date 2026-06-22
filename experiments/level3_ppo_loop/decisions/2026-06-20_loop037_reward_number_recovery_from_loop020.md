# Main-Agent Decision After loop037

Date: 2026-06-20

## Decision

`change_reward_or_training_numbers`

Do not continue:

`v5_decoupled_frame_clearance_low_pressure_reward`

Run the next bounded chunk from the current global-best loop020 checkpoint with
a conservative event-backloaded reward-number retune.

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not promote loop037 as global best.
- Do not continue from loop037 final.
- Do not continue the loop036/loop037 decoupled frame-clearance maturation.
- Keep v5 local-obstacle observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Keep PPO/network/controller structure fixed for the next chunk.
- Change reward/training numbers only through explicit CLI `--param` values.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m`

Best loop037 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m_step_020000000.ckpt`
- Success rate: `0.00`
- Mean successful time: `None`
- Crash rate: `0.85`
- Timeout rate: `0.15`
- Mean gates: `0.60`

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.45`

## Reviewer Synthesis

Evaluator metrics:

- Recommended `change_reward_or_training_numbers`.
- Every loop037 hard-eval checkpoint had `0.00` success.
- The best loop037 checkpoint had only `0.60` mean gates.
- loop037 regressed from loop036's `0.10` success and `1.40` mean gates.
- loop037 also regressed from loop020's `0.15` success and `1.45` mean gates.

W&B/PPO diagnostics:

- Recommended `change_reward_or_training_numbers`.
- `race/passed_gate_rate` tail mean was about `0.00001`.
- `race/finished_rate` stayed `0.0`.
- `race/wrong_side_gate_rate` rose from about `0.0837` to `0.1018`.
- `race/gate_frame_pressure` rose from about `2.14` to `3.35`.
- `reward_components/gate_plane` tail mean was `0.0`.
- PPO movement was weak: `approx_kl` tail about `0.000001`,
  `clipfrac` stayed `0`, and policy loss was near zero.
- Entropy rose while evaluator progress regressed, so extra exploration did
  not become useful gate-pass behavior.

Structure/research synthesis:

- Recommended `launch_named_structural_lane`.
- The reviewer agrees not to continue the loop036/loop037 maturation.
- The failure does not prove v5 observation is bad; it proves this specific
  decoupled frame-clearance low-pressure continuation did not mature.
- A future structural lane may be needed if reward-number recovery from loop020
  fails again, but that must be explicit and separate from this decision.

## Main-Agent Rationale

The main decision is `change_reward_or_training_numbers` because two of three
reviewers recommend it and it is the smaller next intervention.

The rollback anchor should be loop020, not loop036 or loop037:

- loop020 remains the only local branch with `0.15` hard-eval success.
- loop037 erased loop036's non-zero success during the 40M continuation.
- W&B shows the decoupled frame-clearance signal increasing pressure around
  gate frames without producing true pass conversion.

The next retune should restore loop020's `legacy_staged` completion-backloaded
structure and make only a small event-balance adjustment:

- increase true gate/finish event value;
- reduce early front-gate bonus slightly so front-plane contact is less
  attractive than completing the pass;
- increase wrong-side and timeout penalties mildly;
- keep safety/smoothness close to loop020 so gate acquisition is not choked.

## Next Chunk

Run one bounded reward-number recovery chunk:

- Proposal name:
  `v5_loop020_event_backload_wrongside_recovery_20m`
- Initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`
- Reward structure: `legacy_staged`

Changed relative to loop020:

- `gate_axis_coef`: `22.0 -> 24.0`
- `gate_bonus`: `180.0 -> 210.0`
- `gate_front_bonus`: `22.0 -> 16.0`
- `gate_back_bonus`: `95.0 -> 110.0`
- `finish_bonus`: `300.0 -> 320.0`
- `wrong_side_penalty`: `14.0 -> 16.0`
- `crash_penalty`: `50.0 -> 55.0`
- `obstacle_coef`: `4.5 -> 5.0`
- `timeout_penalty`: `80.0 -> 90.0`
- `time_penalty`: `0.005 -> 0.003`

Explicitly reset failed loop037-only frame-clearance parameters:

- `gate_plane_bonus`: `0.0`
- `missed_gate_penalty`: `0.0`
- `gate_frame_pressure_coef`: `0.0`

Keep fixed from loop020:

- PPO/network settings.
- Full 90-degree roll/pitch command authority.
- No action low-pass.
- Smoothness/tilt penalties except for the small crash/obstacle changes above.

## Promotion And Rollback

Promote only if hard eval beats loop020 on at least one primary frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Reject this retune if:

- success remains `0.00`; or
- mean gates stay below `1.00`; or
- wrong-side/gate-frame pressure rises while pass/finish conversion stays flat;
  or
- W&B shows low KL/zero clipfrac and no evaluator progress again.

If this retune fails, the next main-agent decision should prefer a new named
structural lane for direct pass-conversion/aperture-crossing behavior rather
than more small reward-number edits.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --train-timesteps 20000000 \
  --checkpoint-interval 5000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --proposal-name v5_loop020_event_backload_wrongside_recovery_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop037_reward_number_recovery_from_loop020.md \
  --param reward_structure=legacy_staged \
  --param gate_stage_coef=9.0 \
  --param gate_axis_coef=24.0 \
  --param gate_bonus=210.0 \
  --param gate_front_bonus=16.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=110.0 \
  --param finish_bonus=320.0 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=16.0 \
  --param crash_penalty=55.0 \
  --param obstacle_coef=5.0 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=90.0 \
  --param time_penalty=0.003 \
  --param act_coef=0.012 \
  --param d_act_th_coef=0.055 \
  --param d_act_xy_coef=0.055 \
  --param cmd_tilt_coef=0.75 \
  --param rpy_coef=0.65 \
  --param tilt_limit_deg=42.0 \
  --param tilt_excess_coef=10.0 \
  --param action_rp_limit_deg=90.0 \
  --param action_lowpass_alpha=1.0
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
