# Main-Agent Decision After loop045

Date: 2026-06-20

## Trial

- Trial id:
  `level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m`
- Best loop045 checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m_step_010000000.ckpt`
- Hard-eval success rate: `0.15`
- Mean successful time: `5.993333333333333s`
- Crash rate: `0.85`
- Mean gates: `1.20`
- Target met: `false`

## Subagent Findings

- `evaluator_metrics`:
  recommended `continue_same_hypothesis`. loop045 10M ties loop020 on
  success and crash and is faster, but loses mean gates. Continue only from
  the 10M checkpoint, not final.
- `wandb_ppo_diagnostics`:
  recommended `change_reward_or_training_numbers`. PPO did not explode, but
  reward/race signals degraded, finish conversion stayed zero, command
  saturation rose, and 15M-final collapsed to zero hard-eval success.
- `structure_research_synthesis`:
  recommended `continue_same_hypothesis`. Keep v7 and loop020 values long
  enough to mature, but reject if the post-10M collapse repeats.

## Main-Agent Decision

Selected decision:

`change_reward_or_training_numbers`

## Rationale

The v7 observation is not rejected. The 10M checkpoint is real signal:

- Same success as loop020: `0.15`.
- Same crash rate as loop020: `0.85`.
- Faster successful episodes than loop020: `5.99s` vs `6.37s`.

However, original v7 continuation has already been tested from that region:

- 15M: `0.00` success, `1.00` crash.
- 20M: `0.00` success, `1.00` crash.
- 25M: `0.00` success, `1.00` crash.
- Final: `0.00` success, `1.00` crash.
- Command tilt over-limit fraction rose from `0.624` at 10M to `0.817` at
  final.

Therefore, continuing v7 unchanged would repeat a known degeneration path. The
next run should keep the v7 observation and the unchanged `level3_dr.toml`
track, but start from the 10M checkpoint with a stability retune:

- Lower learning rate to reduce destructive continuation updates.
- Add action low-pass and lower roll/pitch action scale.
- Increase crash, tilt, action-change, and command-tilt penalties.
- Remove the small time pressure because successful episodes are already under
  `7s`.
- Keep the same reward structure and gate-completion family; do not change the
  Level3 track.

## Next Lane

Name:

`v7_10m_stability_retune_from_loop045_30m`

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m_step_010000000.ckpt`

Observation layout:

`level3_target_gate_phase_progress_2obs_local_history_v7`

Changed parameters:

- `learning_rate`: `0.0003` -> `0.0001`
- `action_lowpass_alpha`: `1.0` -> `0.65`
- `action_rp_limit_deg`: `90.0` -> `80.0`
- `crash_penalty`: `50.0` -> `75.0`
- `wrong_side_penalty`: `14.0` -> `16.0`
- `obstacle_coef`: `4.5` -> `6.0`
- `obstacle_margin`: `0.3` -> `0.35`
- `time_penalty`: `0.005` -> `0.0`
- `act_coef`: `0.012` -> `0.025`
- `d_act_xy_coef`: `0.055` -> `0.10`
- `d_act_th_coef`: `0.055` -> `0.10`
- `cmd_tilt_coef`: `0.75` -> `1.20`
- `rpy_coef`: `0.65` -> `0.90`
- `tilt_limit_deg`: `42.0` -> `38.0`
- `tilt_excess_coef`: `10.0` -> `16.0`

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v7_explicit_phase_progress_localobs \
  --proposal-name v7_10m_stability_retune_from_loop045_30m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m_step_010000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_045_structural_v7_explicit_phase_progress_localobs_from_loop020_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop045_v7_10m_stability_retune.md \
  --param learning_rate=0.0001 \
  --param action_lowpass_alpha=0.65 \
  --param action_rp_limit_deg=80 \
  --param crash_penalty=75 \
  --param wrong_side_penalty=16 \
  --param obstacle_coef=6 \
  --param obstacle_margin=0.35 \
  --param time_penalty=0.0 \
  --param act_coef=0.025 \
  --param d_act_xy_coef=0.10 \
  --param d_act_th_coef=0.10 \
  --param cmd_tilt_coef=1.20 \
  --param rpy_coef=0.90 \
  --param tilt_limit_deg=38 \
  --param tilt_excess_coef=16
```

If the dry-run is clean, run the same command without `--dry-run`.

## Promotion And Rollback

Promote or mature if any checkpoint beats loop020 on:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success with lower crash/timeout or materially better time and no
  command-saturation regression.

Reject or hold if:

- all checkpoints stay `<=0.15` success and `<=1.20` mean gates;
- the 15M-final collapse repeats;
- command tilt over-limit fraction keeps rising;
- W&B pass/finish conversion remains flat.

## Boundaries

- Do not modify Level3 track geometry, obstacle layout, gate layout, or
  randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch the next chunk without this packet attached via
  `--approved-hypothesis-packet`.
