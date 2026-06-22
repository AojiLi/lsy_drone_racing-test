# Loop066 Decision: Hold For Conversion Diagnosis

## Decision

`hold_for_more_analysis`

Do not launch another train/evaluate chunk yet.

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not accept any result unless it is hard-evaluated on the unchanged Level3
  target track.

## Evidence

Loop066 tested:

`v14_mlp_loop052_constant_lr_directional_pass_conversion_guard`

Best loop066 hard eval:

- Checkpoint: 10M
- success_rate: 0.10
- mean_gates: 1.25
- mean successful time: 6.40s
- crash_rate: 0.90
- timeout_rate: 0.00

Global best remains loop052:

- success_rate: 0.20
- mean_gates: 1.40
- mean successful time: 6.975s
- crash_rate: 0.80

## Subagent Synthesis

Evaluator reviewer:

- Reject v14 maturation.
- 5M/10M/final all stay at 0.10 success, 15M drops to 0.00.
- Mean gates never exceeds 1.25 and final regresses to 1.00.

W&B/PPO reviewer:

- Learning rate is constant and nonzero.
- PPO update pressure is active and not exploding.
- Race conversion is flat: passed gate, finished, and gate-plane crossing do
  not improve.
- Do not continue v14 with more steps.

Structure/research reviewer:

- Reject the narrow v14 hypothesis.
- A possible next direction is a gate-plane center-hit conversion lane, but the
  codebase already has prior `direct_aperture`, `soft_centerline_followthrough`,
  and frame-clearance experiments that did not beat loop052.
- Do not launch a new center-hit lane until a diagnostic explains how it differs
  from those failed lanes.

## Main-Agent Decision

Hold. The current evidence says the loop is in
`hold_plateau_no_conversion`, not in a promising maturation phase.

The next required artifact is a conversion-diagnosis packet comparing loop052,
loop065, and loop066. It must identify the most likely failure mode before
another 20M training run:

- wrong-side approach;
- gate-frame collision;
- obstacle collision near the gate corridor;
- command tilt/action saturation;
- reward event sparsity;
- missing observation signal.

## Next Allowed Action

Allowed:

- Run targeted analysis scripts on existing checkpoints and eval episodes.
- Add or improve analysis scripts if needed.
- Write a new source-backed hypothesis packet after the diagnostic.

Not allowed yet:

- Continue v14 to 60M/90M.
- Launch a simple repeat of `direct_aperture` or `soft_centerline_followthrough`.
- Start another training run without a new diagnostic packet and a new main
  decision packet.
