# Direct Aperture Pass-Conversion Synthesis After loop038

Date: 2026-06-20

## Scope

This packet supports a named Level3 structural lane:

`v5_direct_aperture_crossing_pass_conversion`

Hard boundary:

- Do not modify `config/level3_dr.toml`.
- Train/evaluate acceptance remains hard eval on `config/level3_dr.toml`.
- Keep v5 local-obstacle observations, PPO/network settings, controller, and
  action authority fixed for the next screen.

## Local Evidence

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

Recent failed attempts:

- loop037 continued the decoupled frame-clearance hypothesis from loop036 for
  40M additional steps. Best hard eval regressed to `0.00` success and `0.60`
  mean gates.
- loop038 rolled back to loop020 and tried a conservative event-number retune.
  Best hard eval recovered only to `0.05` success and `1.10` mean gates, still
  below loop020.

W&B/diagnostic evidence from loop038:

- `race/passed_gate_rate` tail mean was about `0.00360` and trended flat/down.
- `race/finished_rate` tail stayed `0.0`.
- `race/wrong_side_gate_rate` rose from about `0.0324` to `0.0424`.
- `reward_components/gate_bonus`, `gate_back`, `gate_front`,
  `gate_stage_progress`, and `gate_axis_progress` trended down.
- PPO was stable enough for a structural reward test:
  `approx_kl` tail about `0.00416`, `clipfrac` tail about `0.00293`,
  and explained variance tail about `0.771`.

## Interpretation

The failure mode is not primarily optimizer instability. The policy receives
gate-approach and event rewards but does not reliably convert them into a
correct, centered pass through the aperture.

The existing staged reward can still pay for partial progress, front hits,
and gate proximity even when pass conversion is weak. The frame-clearance
variants added pressure around the gate frame but did not improve the hard
eval frontier.

The next structural test should make the reward target more literal:

- centered crossing through the gate plane;
- stage-valid gate pass;
- back-plane follow-through;
- explicit missed-plane and wrong-side penalties;
- no new observation or PPO change in the same screen.

## Proposed Lane

Name:

`v5_direct_aperture_crossing_pass_conversion`

Reward structure:

`direct_aperture`

Intended behavior:

- `gate_plane` rewards a stage-valid pass rather than any target change.
- `gate_bonus` rewards only `gate_pass_hit`, meaning the internal front-stage
  condition was satisfied before the environment target changed.
- `gate_front` rewards centered crossing of the gate plane.
- `missed_gate` penalizes crossing the gate plane outside the aperture.
- `gate_frame_pressure` adds a small continuous near-plane off-center penalty.

Fixed from loop020:

- v5 local-obstacle observation layout.
- PPO/network settings.
- Full 90-degree action authority.
- No action low-pass.
- Hard eval on the unchanged Level3 track.

## Promotion And Rollback

Promote or mature only if the lane beats the loop020 frontier on at least one
primary signal:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success with lower crash/timeout or materially better time.

Reject or retune if:

- success remains `0.00`; or
- mean gates stay below `1.00`; or
- W&B `gate_plane_center_hit_rate`, `gate_pass_hit_rate`, and
  `passed_gate_rate` stay flat/down while wrong-side/frame pressure rises.
