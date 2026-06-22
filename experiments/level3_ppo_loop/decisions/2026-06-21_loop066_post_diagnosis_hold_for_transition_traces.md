# Loop066 Post-Diagnosis Decision: Hold For Transition Traces

## Decision

`hold_for_more_analysis`

Do not launch another train/evaluate chunk yet.

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not accept any result unless it is hard-evaluated on the unchanged Level3
  target track.

## Current Best

Global best remains loop052:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`
- success_rate: `0.20`
- mean_gates: `1.40`
- mean successful time: `6.975s`
- crash_rate: `0.80`

## Evidence

Post-loop066 diagnostic packet:

`experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_per_seed_gate_transition_trajectory_diagnosis.md`

Key findings:

- loop065/v13 regressed versus loop052: `0.15` success, `1.25` mean gates,
  `0.85` crash.
- loop066/v14 regressed further: `0.10` success, `1.25` mean gates, `0.90`
  crash.
- v13 moved endpoint failures toward gate side-frame contact.
- v14 moved endpoint failures toward obstacle and pre-plane obstacle contact.
- v14 loses loop052 success seeds `13` and `16`.
- Hidden512 was already rejected by loop061.
- GRU was already rejected by loop062.
- V8 had weak local signal at loop057, but loop058 maturation regressed.

## Subagent Synthesis

Evaluator-metrics reviewer:

- No next training chunk is justified.
- loop052 remains global best at `0.20` success, `1.40` mean gates, `0.80`
  crash.
- hidden512, GRU, v13, and v14 do not satisfy the step-curve maturation rule.
- The only evaluator-supported decision is `hold_for_more_analysis`.

W&B/PPO reviewer:

- PPO does not look collapsed: KL, clip fraction, entropy, and explained
  variance do not indicate optimizer failure.
- Constant LR did not solve conversion.
- `passed_gate_rate`, `finished_rate`, `gate_plane_cross_rate`, and
  `gate_plane_center_hit_rate` stay flat.
- Do not run another immediate continuation, LR tweak, annealing test, or
  reward-number-only 20M chunk.

Structure/research reviewer:

- No materially distinct structural lane is sufficiently supported yet.
- Tried axes already include v8/v9 observation appends, hidden512, GRU,
  constant-LR MLP, v13/v14 conversion reward numbers, and prior
  direct-aperture, soft-centerline, and frame-clearance variants.
- The next artifact should be trace-level per-seed gate-transition diagnosis
  before choosing observation, controller/action smoothing, or curriculum.

## Main-Agent Decision

Hold. The current evidence is strong enough to reject v14 and stale hidden512
follow-up, but not strong enough to launch a new structural lane.

The loop guard was updated so a stale decision packet from an older trial, such
as loop060 hidden512, cannot resolve the pending loop066 post-run gate. A
training packet must now be specific to the pending trial and must choose one
of `continue_same_hypothesis`, `change_reward_or_training_numbers`, or
`launch_named_structural_lane`; a `hold_for_more_analysis` packet is not enough
to unlock training.

## Next Allowed Action

Allowed:

- Add a trace-level diagnostic script or extend the existing crash analysis to
  log the final `1.5s-2.0s` before termination.
- Run that diagnostic on loop052 final, loop065 final, and loop066 10M.
- Write a new decision packet only after that artifact chooses one explicit
  next axis.

Not allowed yet:

- Continue v14 to 60M/90M.
- Launch `v10_hidden512_reward_search_from_best`.
- Relaunch GRU or privileged Critic.
- Launch a simple repeat of direct-aperture, soft-centerline, or
  frame-clearance reward.
- Start another training run using old approval packets from previous trials.
