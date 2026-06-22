# Loop066 Trace-Axis Decision: Hold For Curriculum Packet

## Decision

`hold_for_more_analysis`

Do not launch another train/evaluate chunk yet.

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 target track geometry, gate layout, obstacle layout, or
  randomization.
- Any training-only curriculum must be a named structural lane and must still
  be hard-evaluated on unchanged `config/level3_dr.toml`.

## Evidence

Trace-axis synthesis:

`experiments/level3_ppo_loop/research/2026-06-21_loop066_trace_axis_synthesis.md`

Trace artifacts:

- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_report.md`
- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_summary.json`
- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop052_065_066_gate_transition_trace_trace.csv`

## Main-Agent Synthesis

The next axis is `curriculum/seed-geometry triage`, not another reward-only
run and not immediate controller smoothing.

Reasons:

- loop052 remains the global best at `0.20` success, `1.40` mean gates,
  `0.80` crash, `6.975s` mean successful time.
- loop065 and loop066 regress on hard eval.
- v14 lowers command-tilt over-limit and action saturation versus loop052, yet
  success and crash get worse; this weakens the controller-smoothing hypothesis
  as the immediate next move.
- v13/v14 reward-number changes reshuffle seed outcomes and lose successful
  seeds rather than improving the frontier.
- fixed hard seeds such as `14`, `15`, `17`, `18`, and `20` fail across
  loop052, loop065, and loop066, pointing to geometry-conditioned route
  learning.

## Blocked Training Actions

Do not launch:

- `v10_hidden512_reward_search_from_best`;
- GRU maturation or privileged Critic;
- v14 continuation;
- direct-aperture, soft-centerline, or frame-clearance repeat;
- loop032-style no-wrapper curriculum repeat.

## Next Allowed Action

Write a new named structural curriculum packet and add a matching runnable
orchestrator hypothesis. The packet must explicitly differ from loop032 and
must keep hard eval on `config/level3_dr.toml`.

The next packet should decide whether to create a training-only config or a
sampler/curriculum mechanism that emphasizes the failing seed/geometry cases
without weakening the official hard-eval target.
