# Loop075 Decision: Reject Seed Replay, Launch V20 Default Recovery

Decision: launch_named_structural_lane

Pending gate resolved:

- trial_id: `level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_analysis.json`
- diagnostic_synthesis: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop075_v19_trace_diagnostic_synthesis.md`

## Verdict

Reject loop075 and reject further seed-replay continuation for the next chunk.
Keep loop069 25M as global best.

Current global best on hard eval `config/level3_dr.toml`:

`lsy_drone_racing/control/checkpoints/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt`

- success rate: 0.20
- mean successful time: 6.675s
- crash rate: 0.80
- mean gates: 1.45
- target met: false

Loop075 best:

`lsy_drone_racing/control/checkpoints/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_step_025000000.ckpt`

- success rate: 0.15
- mean successful time: 7.933s
- crash rate: 0.85
- mean gates: 1.55
- target met: false

## Diagnostic Basis

The trace diagnostic shows a replay-overconcentration failure:

- loop071 20M is the only compared checkpoint with non-replay successes:
  2/11 non-replay seeds and 5/20 total successes.
- loop074 20M shifted successes to replay seeds only: 4/9 replay successes,
  0/11 non-replay successes.
- loop075 25M and 30M also had 0/11 non-replay successes.
- PPO/W&B diagnostics do not justify another optimizer change from this
  evidence; the failure is behavioral transfer.

## Next Structural Lane

Launch:

`v20_loop071_default_distribution_recovery_20m`

Contract:

- start from loop071 20M diagnostic frontier
- train on `level3_dr.toml`
- hard eval on `level3_dr.toml`
- do not edit `config/level3_dr.toml`
- use default track-generator distribution, no hard-corridor sampler and no
  seed replay
- keep v5 local-obstacle observation
- keep 2x256 Tanh MLP actor/critic
- keep loop071/v17 reward, PPO, and controller numbers
- train one 20M screening chunk with 5M checkpoint evaluation

## Rollback And Promotion Rule

Promote or mature v20 only if it beats either:

- loop071 diagnostic frontier: success `> 0.25` or mean gates `> 2.00`
  without crash getting worse than `0.75`; or
- loop069 global-best rollback floor: success `>= 0.20`, crash `<= 0.80`,
  and mean successful time near or below `6.675s`.

Reject v20 if it repeats loop075's pattern of zero non-replay success or if it
falls below loop069 on success/crash without a clear mean-gates improvement.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v20_loop071_default_distribution_recovery_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_analysis.md \
  --research-packet experiments/level3_ppo_loop/diagnostics/2026-06-22_loop075_v19_trace_diagnostic_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop075_trace_diagnostic_launch_v20_default_recovery.md
```

If dry-run passes, remove `--dry-run` and run the same command once. After it
finishes, run the analyzer and exactly three subagent reviews before any next
training chunk.
