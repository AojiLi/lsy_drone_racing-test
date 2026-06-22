# Remote Nominal Reward DR Lane Addendum

Date: 2026-06-21

## Scope

- Target remains hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gates, obstacles, or randomization.
- This packet supports one explicit structural lane: try the earlier remote
  nominal safer reward scale on Level3 DR, warm-started from the remote safer
  final checkpoint.

## Source Evidence

Remote notebook history:

`git show 58e8e1a:notebooks/finetune_level3_ppo.ipynb`

The earlier ordinary safer finetune used:

- `TRAIN_ENV_TOML = "level3.toml"`
- `RUN_NAME = "level3_localobs_safer_finetune_from_final"`
- Initial checkpoint:
  `checkpoints/level3_localobs_relax/level3_localobs_relax_final.ckpt`
- `TOTAL_TIMESTEPS_TRAIN = 60_000_000`
- `LEARNING_RATE = 5e-5`
- `NUM_ENVS_TRAIN = 1024`
- `NUM_STEPS = 32`
- `HIDDEN_DIM = 256`
- `ENT_COEF = 0.02`
- `TARGET_KL = 0.03`

Reward numbers from that notebook:

- `progress_coef = 0.0`
- `gate_stage_coef = 10.0`
- `gate_axis_coef = 12.0`
- `near_gate_coef = 0.0`
- `gate_bonus = 90.0`
- `gate_back_bonus = 12.0`
- `finish_bonus = 160.0`
- `missed_gate_penalty = 0.0`
- `wrong_side_penalty = 8.0`
- `crash_penalty = 100.0`
- `obstacle_coef = 8.0`
- `obstacle_margin = 0.40`
- `obstacle_clearance_coef = 6.0`
- `timeout_penalty = 80.0`
- `time_penalty = 0.03`
- `act_coef = 0.03`
- `d_act_th_coef = 0.10`
- `d_act_xy_coef = 0.10`
- `cmd_tilt_coef = 1.0`
- `rpy_coef = 1.0`
- `tilt_limit_deg = 40.0`
- `tilt_excess_coef = 15.0`

Latest remote notebook at `FETCH_HEAD` now records a later
`level3_dr.toml` high-crash-penalty variant:

- `RUN_NAME = "level3_localobs_safer_finetune_from_final_highcrashpenalty"`
- `gate_stage_coef = 15.0`
- `gate_axis_coef = 15.0`
- `gate_bonus = 120.0`
- `gate_back_bonus = 20.0`
- `finish_bonus = 160.0`
- `wrong_side_penalty = 6.0`
- `crash_penalty = 100.0`
- `obstacle_coef = 7.5`
- `obstacle_margin = 0.35`
- `obstacle_clearance_coef = 0.0`

The local hard-eval audit found the earlier ordinary safer final checkpoint
stronger than the high-crash-penalty family on `level3_dr.toml`.

## Local Hard-Eval Evidence

Audit artifacts:

- `experiments/level3_ppo_loop/remote_safer_finetune_level3_dr_eval_summary.csv`
- `experiments/level3_ppo_loop/remote_safer_finetune_level3_dr_eval_episodes.csv`

Best audited remote ordinary safer checkpoint:

`lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final/level3_localobs_safer_finetune_from_final_final.ckpt`

Metrics on `level3_dr.toml`, seeds 1-20:

- Success rate: `0.15`
- Mean successful time: `6.3066666666666675s`
- Crash rate: `0.85`
- Mean gates: `1.45`
- Mean action delta: `0.2959290098141664`
- Mean max commanded tilt: `58.54340936316434deg`
- Commanded tilt over-limit fraction: `0.46296510228667137`

This ties the current global best loop020 on success, crash, and mean gates,
while showing smoother controls and slightly faster successful episodes.

## Loop050/Loop051 Interpretation

loop050 tested the remote safer anchor with loop020-style completion
backloading. It kept `0.15` success but mean gates fell to `1.20`.

loop051 tested a gate-acquisition retune from loop050. It regressed to:

- Success rate: `0.10`
- Crash rate: `0.90`
- Mean gates: `1.15`

W&B pass/finish/gate-plane conversion stayed flat. This falsifies the loop051
retune and argues against continuing the completion-backloaded branch.

## Proposed Lane

Name:

`v5_remote_safer_anchor_nominal_reward_dr_30m`

Hypothesis:

Warm-start from the already-audited remote ordinary safer final checkpoint and
train directly on `level3_dr.toml` using the ordinary safer nominal reward
scale. This tests whether the reward profile that produced the smoother anchor
can adapt to DR without losing gate progress.

This is a structural lane because it enables `obstacle_clearance_coef = 6.0`
and intentionally reverts reward scale from the loop050/loop051 completion and
gate-acquisition retunes.

Promotion:

- success rate `> 0.15`; or
- mean gates `> 1.45`; or
- success `0.15` with mean gates at least `1.45`, crash no worse than `0.85`,
  and smoother action/tilt than loop020.

Rollback:

- all checkpoints stay `<= 0.10` success;
- mean gates stay below `1.20`;
- crash rises above `0.90`;
- W&B gate/finish conversion remains flat while reward rises.
