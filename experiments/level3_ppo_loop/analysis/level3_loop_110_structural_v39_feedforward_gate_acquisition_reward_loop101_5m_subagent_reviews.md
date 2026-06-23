# Loop110 Subagent Reviews

Trial:
`level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m`

Analysis:
`experiments/level3_ppo_loop/analysis/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_analysis.md`

## Evaluator Metrics

Finding: v39 is not a decisive new frontier, but it is promising enough to
mature from its 3M checkpoint.

Best v39 checkpoint:

- checkpoint: step `003000000`
- success: `21%`
- mean gates: `1.64`
- crash: `79%`
- mean successful time: `6.756s`

Comparison:

- vs loop107 1M: same success and crash, `0.02` lower mean gates, `0.822s`
  faster successful time.
- vs loop101 final: `+1pp` success, `-1pp` crash, `0.117s` faster successful
  time, but `0.05` lower mean gates.

Recommendation: `continue_same_hypothesis`, but only from the loop110 3M
checkpoint. Do not continue from final, which regressed to `17%` success /
`1.53` mean gates / `83%` crash.

## W&B / PPO Diagnostics

Finding: PPO remained stable but conservative. The reward rebalance produced a
small intended signal, not a breakthrough.

Evidence:

- `losses/approx_kl`: `0.000231`
- `losses/clipfrac`: `0.0`
- entropy stayed high/flat around `4.426`
- explained variance was about `0.733`
- value loss rose to about `709`
- reward/race signals moved mildly in the intended direction:
  gate bonus, gate-axis progress, gate-stage progress, and passed-gate rate
  improved slightly
- conversion remained weak:
  finish rate stayed tiny, crash remained high, and total reward trended down

Recommendation: continue the same hypothesis from 3M with milestone evals.
Reject if it does not beat `21%` success or recover mean gates beyond the
`1.66` to `1.69` frontier.

## Structure / Research Synthesis

Finding: continue v39 from loop110 3M as a bounded same-hypothesis run. Do not
change reward numbers yet.

Evidence:

- loop110 3M tied the current success frontier at `21%`, improved successful
  time to `6.756s`, and held crash at `79%`.
- It added 8 validation success seeds relative to loop107 1M and lost 8 old
  success seeds, so the signal is a seed-coverage redistribution rather than a
  pure global improvement.
- loop101 is already the v39 parent; plain v37/v37b and v38 retention were
  rejected; more reward scaling before a short maturation would be guesswork.

Recommended next run:

```text
v39b_feedforward_gate_acquisition_seed_expansion_from_loop110_3m
```

Run shape:

- initial checkpoint: loop110 3M
- reward numbers: keep v39 exactly
- config and hard eval: unchanged `config/level3.toml`
- deployment: actor-only PPO
- horizon: short `3M` continuation with dense `0.5M` milestones
- reject if it drifts below `20%` success or remains `<=1.64` mean gates with
  about `80%` contact crashes
- promote only if it beats `21%` success or improves mean gates/crash while
  preserving the seed expansion
