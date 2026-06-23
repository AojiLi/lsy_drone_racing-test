# Loop101 Subagent Reviews

Trial: `level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m`

## Evaluator Metrics

Decision: `launch_named_structural_lane`

- loop101 final tied the headline frontier at `20/100` success and `80%`
  crash, with no timeouts.
- It slightly improved mean gates from the loop097 reference `1.66` to `1.69`
  and mean successful time from about `7.055s` to `6.873s`, but this is not a
  real success-rate break.
- The 8M checkpoint reached `1.81` mean gates, but only `19/100` success and
  `81%` crash, so it is a gate-depth blip rather than a promotion signal.
- Failures remain contact-driven and classified as bounds/ground. Final
  failures by target gate were gate0 `30`, gate1 `17`, gate2 `28`, gate3 `5`.

Recommendation: stop v33 as-is and launch a new named structural lane.

## W&B / PPO Diagnostics

Decision: `launch_named_structural_lane`

- PPO was stable but conservative: KL and clip fraction were tiny, policy loss
  was near zero, entropy remained high, and explained variance stayed usable.
- W&B race metrics did not meaningfully convert: passed-gate, finished, crash,
  and gate-stage signals were mostly flat.
- The analyzer's reward-number command is a generic gate-acquisition template.
  It should not be followed as the next move because W&B reward evidence did
  not convert into hard-eval success.

Recommendation: stop v33 as-is; do not continue same hypothesis or launch
reward-number tuning. Move to PLR / competence-gated curriculum as a named
structural lane.

## Structure / Research Synthesis

Decision: `continue_same_hypothesis`, with PLR as the fallback

- loop101 is not a clean success, but it is also not a complete reject:
  final tied `20%`, improved time, and reached `1.69` mean gates; 8M reached
  `1.81` mean gates.
- If v33 is stopped, the next framework step should be PLR before GRU.
- Boundaries remain: final hard eval on unchanged `config/level3.toml`, no
  track geometry change, and no planner/MPC/shield.

Recommendation: one bounded v33 continuation is acceptable, but if v33 does
not break the frontier, launch PLR next.

## Main-Agent Synthesis

The main-agent decision follows the evaluator and W&B/PPO reviewers. v33 did
not improve success or crash, and two of three reviewers recommended a named
structural lane. The next lane should be a conservative PLR screen, not
reward-number tuning and not a blind v33 continuation.
