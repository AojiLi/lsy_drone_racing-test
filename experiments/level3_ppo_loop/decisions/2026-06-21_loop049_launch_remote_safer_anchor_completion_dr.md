# Main-Agent Decision After loop049 Deep Structural Audit

Date: 2026-06-21

## Decision

`launch_named_structural_lane`

Launch:

`v5_remote_safer_anchor_completion_dr_30m`

## Prior Trial

- Trial:
  `level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m_analysis.md`
- Previous hold packet:
  `experiments/level3_ppo_loop/decisions/2026-06-21_loop049_hold_for_deeper_structural_packet.md`

loop049 best hard eval:

- Success rate: `0.10`
- Mean successful time: `6.30s`
- Crash rate: `0.90`
- Mean gates: `1.05`

Global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

## Three-Review Synthesis

`evaluator_metrics` recommended `launch_named_structural_lane`.

- loop049 regressed against loop020.
- loop047/048 already matured the same local family to a 60M-style point
  without improving loop020.
- No recent branch deserves more maturation on evaluator evidence.

`wandb_ppo_diagnostics` recommended `launch_named_structural_lane`.

- PPO metrics do not show a primary instability failure.
- Rewards rose without converting into hard-eval pass/finish/gate progress.
- The next lane must monitor hard-eval metrics plus W&B pass/finish,
  wrong-side/missed-gate, action/tilt, and PPO diagnostics.

`structure_research_synthesis` recommended `hold_for_more_analysis`.

- Local v5/v6/v7 variants have not produced a clean launch-ready lane.
- The required next work is a deeper structural packet focused on
  pass-through conversion and survival through gates.

The main agent completed the deeper packet:

`experiments/level3_ppo_loop/research/2026-06-21_remote_safer_anchor_completion_dr_synthesis.md`

## New Evidence

Fetched `origin/main` at:

`4201cb16ec725499695f8f58019764b3ad8e3c2c`

Hard-evaluated the newly available safer Level3 checkpoint families on the
unchanged `config/level3_dr.toml`, seeds 1-20.

Artifacts:

- `experiments/level3_ppo_loop/remote_safer_finetune_level3_dr_eval_summary.csv`
- `experiments/level3_ppo_loop/remote_safer_finetune_level3_dr_eval_episodes.csv`

Best remote safer hard-eval checkpoint:

`lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt`

Metrics:

- Success rate: `0.15`
- Mean successful time: `6.3066666666666675s`
- Crash rate: `0.85`
- Mean gates: `1.45`
- Mean action delta: `0.2959290098141664`
- Mean max commanded tilt: `58.54340936316434deg`
- Commanded tilt over-limit fraction: `0.46296510228667137`

This ties loop020 on success, crash, and mean gates, while improving smoothness
and commanded tilt. It does not meet the final target.

The high-crash-penalty remote DR family did not beat loop020 and should not be
continued as-is.

## Main-Agent Rationale

The next lane should start from the ordinary remote safer final checkpoint, not
from loop049 final, loop047/048, or the high-crash-penalty remote checkpoint.

Reason:

- loop020 remains the hard-eval frontier but is aggressive:
  high action delta, high commanded tilt, and high tilt over-limit fraction.
- the remote safer final checkpoint matches loop020's frontier with smoother
  control;
- high-crash-penalty DR finetuning became smoother but lost success;
- completion-backloaded rewards produced the current local frontier in loop020;
- therefore the next useful test is whether the smoother remote anchor can
  retain loop020-level gate progress while loop020-style completion pressure
  pushes pass-through conversion.

This is a named structural/training lane because it changes the initial
checkpoint provenance and learning-rate schedule. It keeps the v5 observation,
legacy reward structure, PPO architecture, and target track fixed.

## Structural Lane

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
- Reward numbers: loop020 completion-backloaded reward values.
- Learning rate: `5e-5`
- PPO architecture: `hidden_dim=256`, `n_obs=2`
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

## Required Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --override-state-hold \
  --proposal-name v5_remote_safer_anchor_completion_dr_30m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_remote_safer_anchor_completion_dr_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop049_launch_remote_safer_anchor_completion_dr.md \
  --param learning_rate=0.00005 \
  --param gamma=0.99 \
  --param gae_lambda=0.95 \
  --param update_epochs=5 \
  --param num_minibatches=8 \
  --param ent_coef=0.02 \
  --param target_kl=0.03 \
  --param hidden_dim=256 \
  --param n_obs=2 \
  --param action_rp_limit_deg=90.0 \
  --param action_lowpass_alpha=1.0 \
  --param reward_structure=legacy_staged \
  --param progress_coef=0.0 \
  --param gate_stage_coef=9.0 \
  --param gate_axis_coef=22.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=180.0 \
  --param gate_front_bonus=22.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=95.0 \
  --param finish_bonus=300.0 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=14.0 \
  --param crash_penalty=50.0 \
  --param obstacle_coef=4.5 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.005 \
  --param act_coef=0.012 \
  --param d_act_th_coef=0.055 \
  --param d_act_xy_coef=0.055 \
  --param cmd_tilt_coef=0.75 \
  --param rpy_coef=0.65 \
  --param tilt_limit_deg=42.0 \
  --param tilt_excess_coef=10.0
```

If dry-run passes, run the same command without `--dry-run`.

## Promotion And Rollback

Promote if hard eval on `config/level3_dr.toml` beats loop020:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- success `0.15` with mean gates at least `1.45`, crash no worse than `0.85`,
  and materially better action/tilt stability plus improving W&B pass/finish
  conversion.

Hold or reject if:

- all checkpoints stay `<=0.10` success;
- mean gates stay below `1.45`;
- crash stays `>=0.90`;
- final or late milestones collapse to `0.00` success;
- W&B reward rises without `passed_gate_rate`, `finished_rate`, or
  `gate_plane_cross_rate` conversion.

After this chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then repeat the three-review decision gate before any further training.
