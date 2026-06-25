# V54 Reference Tracker Decision: Hold Long Training

Created: 2026-06-25

Decision: `hold_for_more_analysis`

Lane: `v54_reference_trajectory_tracker_ppo`

Analysis packet:

`experiments/level3_ppo_loop/analysis/2026-06-25_v54_reference_tracker_long_training_prep.md`

## Decision

Do not launch the manual long-training command yet.

No long-training terminal command is approved from this packet.

## Evidence

The final strict smoke used unchanged `config/level3.toml`, checkpoint-backed
v54 controller loading, and validation seeds `101-120`.

Best diagnostic checkpoint:

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_gate_aperture_lr1e4_32k.ckpt`

Best diagnostic smoke:

- all finite: `true`;
- checkpoint-backed: `true`;
- nonzero first-gate progress: `14 / 20`;
- gate-0 pass count: `0 / 20`;
- early termination before 50 steps: `18 / 20`;
- long-training gate: `false`;
- readiness failure: `no_seed_passed_gate_0`.

The later rp35 Level3-stability checkpoint also failed:

- nonzero first-gate progress: `13 / 20`;
- gate-0 pass count: `0 / 20`;
- early termination before 50 steps: `18 / 20`;
- long-training gate: `false`.

## Why This Holds

The tracker now has a valid training/evaluation pipeline, but not a credible
behavioral base for long training. The bounded diagnostics show movement toward
gate 0, not gate completion. The problem is not yet "needs more overnight
steps"; it is "has not learned the local gate crossing subskill."

## Required Next Work

Before reconsidering long training, create a v54 gate-aperture completion
curriculum:

- reset starts near the current gate in pre-gate, align, cross, and recover
  phases;
- explicitly reward safe plane crossing / phase completion;
- keep `config/level3.toml` unchanged for final smoke;
- require mini-task gate crossing before Level3 seeds `101-120`;
- keep strict readiness: majority first-gate progress and at least one gate-0
  pass.
