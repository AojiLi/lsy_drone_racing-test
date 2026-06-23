# Decision: Loop111 Interrupted, Keep V39B Diagnostic Scope

Decision: `hold_for_more_analysis`

## Status

`level3_loop_111_structural_v39b_feedforward_gate_acquisition_loop110_3m_3m`
was interrupted before completing training and before any hard evaluation.

Observed partial artifact:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_111_structural_v39b_feedforward_gate_acquisition_loop110_3m_3m/level3_loop_111_structural_v39b_feedforward_gate_acquisition_loop110_3m_3m_step_000500000.ckpt`
- completed hard eval: none
- conclusion: none

This partial run must not be used as evidence for or against v39b.

## Diagnostic Policy

The user and main agent agree that the current 21% success plateau is unlikely
to be solved by small reward-number tuning alone. v39/v39b is useful as a
diagnostic of the gate-acquisition reward direction, but it should not be
treated as the main route to the 60% target.

A completed v39b run is worth continuing only if hard eval on unchanged
`config/level3.toml` clearly breaks the plateau, for example:

- success moves beyond 21% toward roughly 25%-30%;
- crash rate drops meaningfully while success is preserved or improved;
- mean gates improves without simply swapping one set of success seeds for
  another;
- success-rate improvement matters more than faster mean successful time.

If v39b remains around 18%-22%, only reshuffles solved seeds, or improves speed
without success/crash conversion, stop reward-number small-tuning and pivot to
a named structural lane focused on training distribution, memory/strategy,
observation, or anti-drift stability.

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry or randomization.
- Do not count the interrupted loop111 partial checkpoint as a promotion.
- A restart of the same v39b diagnostic is allowed, but it must complete the
  normal train/evaluate/analyze/subagent-review/decision cycle before any next
  training chunk.
