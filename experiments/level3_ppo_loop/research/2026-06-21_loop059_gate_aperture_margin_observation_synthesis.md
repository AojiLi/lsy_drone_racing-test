# Loop059 Gate-Aperture Margin Observation Synthesis

Date: 2026-06-21

## Scope

- Target hard eval remains `config/level3_dr.toml`.
- Level3 track geometry, gates, obstacles, and randomization are immutable.
- This packet supports one bounded structural observation lane:
  `v9_gate_aperture_margin_obs_from_loop052_30m`.
- The lane starts from the current global-best loop052 checkpoint.
- It keeps loop052 reward numbers, controller settings, PPO learning rate,
  update epochs, target KL, network size, and action scaling fixed.
- It changes only the observation layout by appending explicit current-gate
  aperture margin features.

## Local Hard-Eval Evidence

Current global best:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Hard eval on `config/level3_dr.toml`, seeds 1-20:

- Success: `0.20`
- Mean successful time: `6.975s`
- Crash: `0.80`
- Mean gates: `1.40`

Loop059 low-entropy exploitation failed:

- Best success: `0.10`
- Mean gates: `1.20`
- Crash: `0.90`
- Mean successful time: `7.13s`

Loop059 W&B improved some reward proxies and reduced entropy, but hard eval
regressed. This rejects another entropy/PPO-number move.

## Crash Taxonomy Evidence

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_052_final_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_057_25M_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_058_final_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_059_final_20seed_crash_taxonomy_summary.json`

Loop059 diagnostic replay:

- Successes: `2 / 20`
- Crashes: `18 / 20`
- Crash target gates: gate0 `8`, gate1 `3`, gate2 `6`, gate3 `1`
- Nearest gate parts: right `10`, stand `3`, bottom `2`, left `2`, top `1`
- Likely objects: obstacle2 `4`, obstacle0 `3`, obstacle3 `2`, plus right
  gate-frame hits.

Comparison:

- loop052 crashes are spread across left/right/bottom/stand/top gate parts.
- loop057 v8 reduced some early gate0 crashes but did not beat loop052.
- loop058 v8 maturation lost the weak v8 benefit.
- loop059 shows a sharper right-side gate-frame concentration.

Interpretation:

The remaining failure is not speed. It is gate/obstacle pass conversion, with a
visible gate-frame side-margin failure mode. v8 appended nearest-obstacle
gate-corridor geometry, but did not directly expose square aperture margins
inside the current gate plane.

## Proposed Observation Lane

Name:

`v9_gate_aperture_margin_obs_from_loop052_30m`

Observation layout:

`level3_gate_aperture_margin_2obs_local_history_v9`

Base layout:

`level3_target_gate_nearest_gate_2obs_local_history_v5`

Append one 9-float current-gate aperture block:

- target progress;
- drone position in current gate frame: x, y, z;
- signed left margin: `y + 0.2`;
- signed right margin: `0.2 - y`;
- signed bottom margin: `z + 0.2`;
- signed top margin: `0.2 - z`;
- radial margin: `0.2 - norm([y, z])`.

The gate corners already contain enough information in principle, but the
append exposes the safety-relevant aperture quantities directly to the MLP.
This is different from:

- v6, which replaced nearest-other-gate with race-order next gate;
- v7, which appended only phase/progress and gate-frame position;
- v8, which appended nearest obstacle geometry in the current gate frame;
- loop059, which changed entropy pressure only.

## Proposed Settings

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Training setup:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

Keep fixed from loop052:

- reward structure and reward numbers;
- `learning_rate=5e-5`;
- `ent_coef=0.02`;
- `update_epochs=5`;
- `num_minibatches=8`;
- `target_kl=0.03`;
- `hidden_dim=256`;
- `action_rp_limit_deg=90`;
- `action_lowpass_alpha=1.0`.

Warm start:

Zero-pad the appended input weights from loop052. This preserves the initial
loop052 policy neighborhood while giving the policy a chance to learn the new
aperture-margin features.

## Promotion And Rollback

Promote if the best hard-eval checkpoint reaches at least one:

- success `>0.20`;
- success `0.20` with mean gates `>1.40` and crash `<=0.80`;
- mean gates `>1.45` with nonzero success;
- right-side gate-frame crash share decreases materially versus loop059 while
  success stays at least `0.20`.

Reject if:

- all checkpoints stay `<=0.15` success;
- mean gates stay below `1.40`;
- crash stays `>=0.85`;
- W&B gate/finish signals stay flat;
- crash taxonomy still concentrates on right gate-frame hits without evaluator
  improvement.

## Boundaries

- Do not modify `config/level3_dr.toml` track geometry or randomization.
- Do not edit `notebooks/train_level3_ppo.ipynb`.
- Do not continue v8.
- Do not continue the low-entropy lane.
- Do not change reward numbers in this lane.
