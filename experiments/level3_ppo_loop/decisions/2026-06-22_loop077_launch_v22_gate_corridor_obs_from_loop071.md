# Loop077 Decision: Launch V22 Gate-Corridor Observation Screen

Decision: launch_named_structural_lane

Source packets:

- loop077 rejection:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop077_reject_v21_hold_for_trace_diagnostics.md`
- trace synthesis:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop077_v21_trace_diagnostic_synthesis.md`
- trace report:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop069_071_076_077_v21_trace_diagnostic_report.md`

## Verdict

Launch one bounded v22 screen. Do not continue v21. Do not rerun the same
strong gate-acquisition reward numbers. Do not return to seed replay or naive
loop071 maturation.

## Lane

`v22_loop071_gate_corridor_obstacle_obs_default_20m`

Contract:

- initial checkpoint: loop071 20M
- train config: `level3_dr.toml`
- hard eval config: unchanged `level3_dr.toml`
- observation layout:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- PPO/training numbers: unchanged from the loop071/v17 nominal family
- controller settings: unchanged
- reward structure: `legacy_staged`
- reward numbers: unchanged nominal loop071 values
- track generator profile: `default`
- horizon: 20M with 5M checkpoint evaluation

## Rationale

The latest trace diagnostic rejected v21 because higher gate reward pressure
made near-gate obstacle/frame collisions worse and did not recover the loop071
20M frontier. Loop071 remains the strongest diagnostic checkpoint at 0.25
success and 2.00 mean gates, but plain continuation and seed-replay maturation
have already been rejected.

The next useful test is therefore structural but narrow: keep training,
reward, controller, and PPO numbers fixed while changing only the local
observation layout to expose gate-corridor obstacle geometry. The existing
training code supports zero-padding warm-start from v5 local-obstacle
checkpoints, so this tests whether the loop071 policy neighborhood can use the
additional geometry without discarding its learned behavior.

## Promotion Rule

Promote or mature v22 only if a milestone beats one of:

- loop071 frontier: success `> 0.25`, or mean gates `> 2.00` with crash
  `<= 0.75`
- loop069 global-best floor: success `>= 0.20`, crash `<= 0.80`, and mean
  successful time near or below `6.675s`
- clear retention signal: success `>= 0.20` and a broader fixed-seed success
  set than loop077/v21 without higher crash

Reject or hold if every milestone stays below 0.20 success and no checkpoint
improves mean gates or crash behavior versus loop071/loop069.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v22_loop071_gate_corridor_obstacle_obs_default_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/diagnostics/2026-06-22_loop077_v21_trace_diagnostic_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop077_launch_v22_gate_corridor_obs_from_loop071.md
```
