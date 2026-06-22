# Soft Centerline Saturation Guard Synthesis After loop041

Date: 2026-06-20

## Scope

This packet supports a named Level3 structural lane:

`v5_soft_centerline_saturation_guard_pass_conversion`

Hard boundary:

- Do not modify `config/level3_dr.toml`.
- Train/evaluate acceptance remains hard eval on `config/level3_dr.toml`.
- Keep v5 local-obstacle observations.
- Keep PPO/network settings.
- Keep full 90-degree action authority.
- Add only a mild controller action low-pass guard.

## Local Evidence

Current global best remains loop020:

- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`
- Mean action delta: `0.3672461037185129`
- Commanded tilt over-limit fraction: `0.5800860395510893`

loop040 soft-centerline screen:

- Best hard eval: `0.10` success, `1.15` mean gates, `0.90` crash.
- Best checkpoint was the 5M checkpoint.
- Later checkpoints regressed, but the lane restored non-zero success after
  direct-aperture failed.

loop041 soft-centerline reward-number retune:

- Best hard eval: `0.05` success, `0.85` mean gates, `0.95` crash.
- Mean successful time was `4.6s`, but this came from one successful episode
  and is not enough to offset the lower success and gate progress.
- Mean action delta rose to `0.6610376674044506`.
- Mean max commanded tilt rose to `85.40291358610486deg`.
- Commanded tilt over-limit fraction rose to `0.7464038983326822`.
- W&B showed `finished_rate` stayed zero, `passed_gate_rate` remained flat,
  `gate_plane_center_hit_rate` nearly vanished, and wrong-side/frame-pressure
  signals stayed high.

Prior low-pass evidence:

- loop025 tested strong low-pass with `action_lowpass_alpha=0.35`; it reduced
  command saturation but did not beat the loop020 frontier.
- loop034 tested mild low-pass with `action_lowpass_alpha=0.65` under the
  legacy staged reward structure; it improved smoothness/saturation but did not
  preserve enough pass conversion.

## Interpretation

loop041 did not fail because the model lacked more dense gate reward. It failed
because stronger dense gate acquisition increased aggressive commands without
turning approach geometry into stable centered passes.

The next test should not keep pushing reward numbers. It should test whether
the now-viable soft-centerline reward structure benefits from the same mild
saturation guard that previously reduced command aggression, while avoiding
the strong low-pass setting that was too restrictive.

The test is still a bounded screen, not a promotion:

- use loop040's original soft-centerline reward balance;
- add `action_lowpass_alpha=0.65`;
- keep `action_rp_limit_deg=90.0`;
- start from the global-best loop020 checkpoint, not the regressed loop041
  policy;
- evaluate all checkpoints on the unchanged Level3 track.

## Proposed Lane

Name:

`v5_soft_centerline_saturation_guard_pass_conversion`

Controller/reward structure:

- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure:
  `soft_centerline_followthrough`
- Action low-pass:
  `action_lowpass_alpha=0.65`
- Action authority:
  `action_rp_limit_deg=90.0`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

## Promotion And Rollback

Promote or mature only if the lane beats loop020 on at least one primary
signal:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success with lower crash/timeout or materially better time.

Reject or hold if:

- success stays `<=0.10`; or
- mean gates stay below `1.45`; or
- crash stays `>=0.95`; or
- pass/center-hit metrics stay flat while wrong-side/frame pressure remains
  high.

If this lane fails, stop doing repeated soft-centerline reward-number nudges and
hold for a deeper observation/controller redesign packet.
