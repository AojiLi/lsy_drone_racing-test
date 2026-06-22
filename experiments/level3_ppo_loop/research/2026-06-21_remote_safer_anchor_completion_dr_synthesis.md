# Remote Safer Anchor Completion-DR Synthesis After loop049

Date: 2026-06-21

## Scope

- Target remains hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue loop049, loop047, or loop048.
- Use the latest stateirving remote checkpoint evidence only as a source of
  warm-start and training-lane hypotheses.

## Current Local Frontier

Global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`
- Mean action delta: `0.3672461037185129`
- Mean max commanded tilt: `70.64878363598818deg`
- Commanded tilt over-limit fraction: `0.5800860395510893`

loop049 failed the no-damping isolation check:

- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m_step_015000000.ckpt`
- Success rate: `0.10`
- Mean successful time: `6.30s`
- Crash rate: `0.90`
- Mean gates: `1.05`

## Remote Latest Evidence

Fetched `origin/main` at `4201cb16ec725499695f8f58019764b3ad8e3c2c`.
The new remote change added two Level3 local-observation finetune checkpoint
families and updated `notebooks/finetune_level3_ppo.ipynb`.

The notebook records a warm-start plan from
`checkpoints/level3_localobs_relax/level3_localobs_relax_final.ckpt` with:

- `num_envs=1024`
- `num_steps=32`
- `hidden_dim=256`
- `learning_rate=5e-5`
- `ent_coef=0.02`
- `target_kl=0.03`
- v5 local-obstacle observation layout

The latest notebook DR finetune variant uses a safer reward profile:

- `gate_stage_coef=15`
- `gate_axis_coef=15`
- `gate_bonus=120`
- `gate_back_bonus=20`
- `finish_bonus=160`
- `wrong_side_penalty=6`
- `crash_penalty=100`
- `obstacle_coef=7.5`
- `obstacle_margin=0.35`
- `time_penalty=0.03`
- `act_coef=0.03`
- `d_act_th_coef=0.10`
- `d_act_xy_coef=0.10`
- `cmd_tilt_coef=1.0`
- `rpy_coef=1.0`
- `tilt_limit_deg=40`
- `tilt_excess_coef=15`

## New Hard-Eval Audit

Command:

```bash
pixi run -e gpu python scripts/evaluate_level2_selected_ppo.py \
  --config level3_dr.toml \
  --seed-start 1 \
  --num-seeds 20 \
  --inference-module ppo_level3_inference \
  --out-prefix experiments/level3_ppo_loop/remote_safer_finetune_level3_dr_eval \
  <10 remote safer checkpoints>
```

Artifacts:

- `experiments/level3_ppo_loop/remote_safer_finetune_level3_dr_eval_summary.csv`
- `experiments/level3_ppo_loop/remote_safer_finetune_level3_dr_eval_episodes.csv`

Best audited checkpoint:

`lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt`

Metrics on `level3_dr.toml`, seeds 1-20:

- Success rate: `0.15`
- Mean successful time: `6.3066666666666675s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.45`
- Mean action delta: `0.2959290098141664`
- Mean max tilt: `33.88496861428428deg`
- Mean max commanded tilt: `58.54340936316434deg`
- Commanded tilt over-limit fraction: `0.46296510228667137`

This ties loop020 on success, crash, and mean gates, with slightly faster
successful episodes and substantially smoother command/tilt metrics.

The high-crash-penalty DR family did not beat loop020:

- Best high-crash success rate: `0.10`
- Best high-crash mean gates: `1.25`
- Best high-crash crash rate: `0.90`

## Interpretation

The latest remote checkpoint audit does not meet the target and does not
strictly beat loop020 on success. It does show a useful new anchor:

- same hard-eval frontier as loop020;
- lower action delta;
- lower commanded tilt;
- lower tilt over-limit fraction;
- no degradation in mean gates or crash at the final ordinary safer checkpoint.

That means the next lane should not simply continue the high-crash-penalty
reward profile. That profile produced smoother behavior but lower success in
hard eval.

The next falsifiable hypothesis is narrower:

Start from the remote safer final anchor, keep the v5 local observation layout,
and fine-tune on `level3_dr.toml` with the loop020 completion-backloaded reward
numbers and a low finetune learning rate. This tests whether the smoother
remote anchor can keep loop020-level gate progress while the completion-heavy
reward pushes more full gate traversals.

Recent failed lanes do not already falsify this:

- loop026 matured loop020 from the loop020 checkpoint, not from the smoother
  remote safer anchor.
- loop047/048 used loop020 or loop047 anchors with moderate PPO/damping, not
  the remote safer anchor.
- loop049 removed damping from loop020 and regressed.
- the high-crash-penalty remote DR family changed the reward toward safety and
  did not preserve success; the proposed lane instead uses the loop020
  completion-backloaded reward.
- v6/v7 observation lanes changed observation semantics; this lane keeps the
  strongest v5 observation.

## Proposed Lane

Name:

`v5_remote_safer_anchor_completion_dr_30m`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `legacy_staged`
- Reward numbers: loop020 completion-backloaded values.
- Training change: low finetune learning rate `5e-5`, keeping PPO structure
  otherwise at the v5/loop020 family values.
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

## Promotion And Rollback

Promote if hard eval on `config/level3_dr.toml` beats loop020:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- success `0.15` with mean gates at least `1.45`, crash no worse than `0.85`,
  and materially better action/tilt stability plus improving W&B pass/finish
  conversion.

Reject or hold if:

- all checkpoints stay `<=0.10` success;
- mean gates stay below `1.45`;
- crash stays `>=0.90`;
- late checkpoints collapse to `0.00` success;
- W&B reward rises but `passed_gate_rate`, `finished_rate`, and
  `gate_plane_cross_rate` remain flat.

If the 30M screen beats or cleanly ties the frontier with better conversion,
consider maturing the same anchor toward 60M under the Level2 step-curve rule.
