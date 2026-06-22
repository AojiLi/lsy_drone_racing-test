# Loop076 Decision: Launch V21 Gate-Acquisition Reward Screen

Decision: launch_named_structural_lane

Source decision:

- `experiments/level3_ppo_loop/decisions/2026-06-22_loop076_reject_v20_hold_for_v21_gate_obstacle_frame_recovery.md`

Analysis packet:

- `experiments/level3_ppo_loop/analysis/level3_loop_076_structural_v20_loop071_default_distribution_recovery_20m_analysis.md`

Research/synthesis packet:

- `experiments/level3_ppo_loop/research/2026-06-22_loop076_v21_gate_acquisition_reward_synthesis.md`

## Verdict

Launch one bounded v21 screen. Do not continue v20. Do not return to seed
replay. Do not change PPO/training numbers, observation layout, controller, or
network size.

## Lane

`v21_default_gate_obstacle_frame_recovery_from_loop071_20m`

Contract:

- initial checkpoint: loop071 20M
- train config: `level3_dr.toml`
- hard eval config: `level3_dr.toml`
- observation: v5 local-obstacle
- policy: 2x256 Tanh MLP
- PPO/training numbers: unchanged from loop071/v20
- track generator profile: `default`
- reward structure: `legacy_staged`
- horizon: 20M with 5M checkpoint evaluation

Reward-number change:

- strengthen gate acquisition and pass conversion:
  `gate_stage_coef=13`, `gate_axis_coef=24`, `gate_front_bonus=5`,
  `gate_bonus=200`, `gate_back_bonus=35`, `finish_bonus=175`
- reduce time pressure slightly: `time_penalty=0.02`
- keep obstacle/crash/smoothness/safety numbers unchanged

## Rationale

Loop076 showed that default-distribution recovery alone did not preserve
loop071's frontier. W&B/PPO diagnostics were stable, so the next test should
not tune PPO. Prior large reward-structure swaps were weak, so v21 uses the
existing `legacy_staged` reward and changes only a bounded set of gate
acquisition/pass-conversion numbers.

## Rollback Rule

Reject v21 if it fails to beat loop069's 0.20 success / 0.80 crash rollback
floor and fails to beat loop071's 2.00 mean-gates frontier at any milestone.

Promote or mature only if a milestone reaches:

- success `> 0.25`, or
- mean gates `> 2.00` with crash `<= 0.75`, or
- success `>= 0.20`, crash `<= 0.80`, and mean successful time near/below
  6.675s.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v21_default_gate_obstacle_frame_recovery_from_loop071_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_076_structural_v20_loop071_default_distribution_recovery_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_loop076_v21_gate_acquisition_reward_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop076_launch_v21_gate_acquisition_reward_from_loop071.md
```
