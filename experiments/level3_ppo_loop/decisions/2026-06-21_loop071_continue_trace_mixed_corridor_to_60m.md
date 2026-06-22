# Loop071 Decision: Continue V17 Trace-Mixed Corridor To 60M

Decision: continue_same_hypothesis

Pending gate resolved:

- trial_id: `level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m_analysis.json`

## Verdict

Continue the v17 trace-mixed corridor hypothesis from its best 20M checkpoint.
Do not apply the analyzer's broad reward-number retune yet.

Best loop071 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m/level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m_step_020000000.ckpt`

Metrics on hard eval `config/level3_dr.toml`:

- success rate: 0.25
- mean successful time: 8.524s
- crash rate: 0.75
- mean gates: 2.00
- target met: false

This improves over the loop069 hard-eval anchor on success, mean gates, and
crash rate, but not on time:

- loop069 25M: 0.20 success, 1.45 mean gates, 0.80 crash, 6.675s
- loop071 20M: 0.25 success, 2.00 mean gates, 0.75 crash, 8.524s

The loop071 final checkpoint regressed, so milestone-aware checkpoint selection
is required. Do not assume final is best.

## Subagent Consensus

- evaluator metrics: promote v17 to a 60M maturation from the loop071 20M
  checkpoint; reject only if no milestone beats 0.25 success or 2.00 mean gates.
- W&B/PPO diagnostics: PPO is stable; the problem is fragile evaluator
  conversion, not optimizer blow-up. Do not increase time pressure yet because
  success is still low.
- structure/research synthesis: continue the same v17 structural signal and do
  not confound it with a broad reward retune.

## Next Lane

Use structural hypothesis:

`v17_trace_mixed_corridor_maturation_from_loop071_20m`

Contract:

- start from loop071 20M checkpoint
- train 40M additional steps, reaching a 60M-level v17 maturation horizon
- checkpoint every 5M
- keep training config `level3_dr.toml`
- keep hard eval `config/level3_dr.toml`
- keep v5 local-obstacle observation
- keep 2x256 MLP actor/critic
- keep loop052 nominal reward numbers
- keep constant learning rate 5e-5
- keep training-only `track_generator_profile=trace_mixed_corridor`
- do not edit `config/level3_dr.toml`

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --allow-step-curve-maturation \
  --structural-hypothesis v17_trace_mixed_corridor_maturation_from_loop071_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop071_continue_trace_mixed_corridor_to_60m.md
```

## Rollback Rule

Reject v17 maturation if no checkpoint milestone beats 0.25 success or 2.00
mean gates, or if crash regresses above 0.80 without compensating gate progress.
If success/gates improve but time remains above 7.0s, consider a narrow
time-pressure or smoothness retune only after this 60M maturation evidence.
