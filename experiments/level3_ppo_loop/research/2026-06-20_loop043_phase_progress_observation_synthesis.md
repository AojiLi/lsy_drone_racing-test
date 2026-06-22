# Explicit Phase/Progress Observation Synthesis After loop043

Date: 2026-06-20

## Scope

This packet supports a named Level3 structural lane:

`v7_explicit_phase_progress_localobs`

Hard boundary:

- Do not modify `config/level3_dr.toml`.
- Final acceptance remains hard eval on `config/level3_dr.toml`.
- Do not continue v6 unchanged.
- Do not apply the analyzer's generic gate-acquisition reward-number retune.

## Evidence From loop043

loop043 tested:

`v6_next_gate_localobs_warmstart`

It replaced v5's nearest-other gate block with the race-order next gate while
keeping the same 68-dimensional local observation family and loop020 frontier
reward/PPO values.

Best hard-eval checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m/level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m_step_020000000.ckpt`

Metrics:

- Success rate: `0.10`
- Mean successful time: `5.220000000000001s`
- Crash rate: `0.90`
- Timeout rate: `0.00`
- Mean gates: `1.00`
- Mean action delta: `0.5919294721125905`
- Command tilt over-limit fraction: `0.7708399421649925`

Checkpoint curve:

- 10M: `0.05` success, `1.00` mean gates, `0.95` crash.
- 15M: `0.00` success, `0.95` mean gates, `1.00` crash.
- 20M: `0.10` success, `1.00` mean gates, `0.90` crash.
- 25M: `0.00` success, `0.75` mean gates, `1.00` crash.
- Final: `0.10` success, `0.95` mean gates, `0.90` crash.

loop043 did not beat loop020:

- loop020 success: `0.15`
- loop020 mean gates: `1.45`
- loop020 crash: `0.85`
- loop020 mean successful time: `6.366666666666667s`

## W&B/PPO Diagnosis

W&B/PPO review found:

- PPO numerics were stable, not explosive.
- Late updates were weak: KL `0.000143`, clipfrac `0`, policy loss near zero,
  entropy rising to `10.53`.
- `gate_stage` and `gate_axis` improved somewhat, but did not convert to
  plane crossing or completion.
- `passed_gate_rate` fell, `finished_rate` stayed `0`, wrong-side rate rose,
  and command saturation worsened.
- Reward components worsened: `train/total_reward` fell to `-76460`, finish
  bonus stayed effectively zero, and pass/front/back components declined.

This argues against simply maturing v6 or applying another reward-number
gate-acquisition nudge.

## Reviewer Synthesis

Evaluator reviewer:

- Recommended `continue_same_hypothesis` because loop043 had non-zero success
  and fast successful episodes.

W&B/PPO reviewer:

- Recommended `launch_named_structural_lane`.
- Reason: training signals did not convert into evaluator progress and command
  saturation worsened.

Structure/research reviewer:

- Recommended `launch_named_structural_lane`.
- Reason: v6 triggered its own rollback conditions and v5/v6 local gate
  semantics have not produced stable pass-through.

Main synthesis:

The minority continuation argument is valid only under the broad step-curve
rule that non-zero success can deserve maturation. Here, the lane-specific
rollback criteria are stronger: loop043 stayed `<=0.10` success, mean gates
never exceeded `1.00`, pass/finish conversion stayed flat, and command
saturation increased. Therefore v6 should not be matured unchanged.

## Hypothesis

v5 and v6 both encode local gate geometry, but neither gives the policy an
explicit scalar race phase and current gate-frame progress state.

The policy may be wasting capacity inferring:

- which race phase it is in;
- whether it is before, centered on, or past the current gate plane;
- how far it is laterally from the current gate centerline.

The proposed v7 layout keeps the loop020 v5 68-dimensional observation order
intact and appends 4 explicit features:

- `target_progress`: normalized target gate index;
- current gate-frame `x`;
- current gate-frame `y`;
- current gate-frame `z`.

This preserves the loop020 input semantics for the first 68 dimensions and
adds compact phase/progress information at the end.

## Proposed Lane

Name:

`v7_explicit_phase_progress_localobs`

Observation layout:

`level3_target_gate_phase_progress_2obs_local_history_v7`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Warm-start method:

- Copy v5 checkpoint weights into the v7 model.
- Keep the original 68 input columns aligned.
- Zero-pad first-layer actor/critic weights for the 4 appended features.
- Start optimizer fresh.

Code/config knobs:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Reward/PPO/controller values: loop020 frontier values.
- Timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`

## Promotion And Rollback

Promote or mature toward 60M if any checkpoint beats loop020 on at least one
primary frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Reject or hold if:

- success stays `<=0.10`;
- mean gates stay near `1.0`;
- crash stays `>=0.90`;
- W&B pass/finish conversion remains flat;
- command tilt saturation keeps rising.

If v7 fails, the next stage should hold for a broader controller/training
structure review rather than continuing local observation variants.
