# Loop074 Decision: Continue V19 Low-Probability Replay To 60M

Decision: continue_same_hypothesis

Pending gate resolved:

- trial_id: `level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m_analysis.json`

## Verdict

Continue v19 from the loop074 20M checkpoint toward a 60M-level maturation
decision. Do not continue from loop074 25M or final. Do not apply the analyzer's
generic gate-acquisition reward-number command yet.

Best loop074 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m/level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m_step_020000000.ckpt`

Metrics on hard eval `config/level3_dr.toml`:

- success rate: 0.20
- mean successful time: 7.755s
- crash rate: 0.80
- mean gates: 1.60
- target met: false

Comparison:

- loop069 25M global best: 0.20 success, 1.45 mean gates, 0.80 crash, 6.675s
- loop071 20M diagnostic frontier: 0.25 success, 2.00 mean gates, 0.75 crash, 8.524s
- loop074 20M: 0.20 success, 1.60 mean gates, 0.80 crash, 7.755s

Loop074 passes the v19 rollback floor by restoring 0.20 success with crash
0.80 and improving mean gates versus loop069. It does not pass the stronger
promotion frontier from loop071.

## Subagent Consensus

Evaluator metrics:

- `continue_same_hypothesis`.
- v19 passed rollback but not promotion.
- Continue only from loop074 20M; keep loop069 25M as the global best because
  loop074 ties success/crash but is slower.

W&B/PPO diagnostics:

- PPO is stable enough: KL/clip fraction are low and flat, entropy is healthy,
  and value loss is not diverging.
- W&B gate and finish curves do not justify a reward-number escalation.
- Continue v19 unchanged from loop074 20M rather than applying the analyzer's
  reward command.

Structure/research synthesis:

- Continue v19 to a 60M-level maturation from loop074 20M.
- Applying new gate-acquisition reward numbers now would confound the
  low-probability replay signal before the maturation test.
- Hard eval remains on unchanged `config/level3_dr.toml`.

## Next Lane

Launch named structural maturation lane:

`v19_trace_seed_replay_lowprob_success_retention_maturation_from_loop074_20m`

Contract:

- start from loop074 20M checkpoint
- keep v5 local-obstacle observation
- keep 2x256 MLP actor/critic
- keep loop052 nominal reward numbers
- keep constant learning rate 5e-5
- keep training config `level3_dr.toml`
- keep hard eval `config/level3_dr.toml`
- keep training-only `track_generator_profile=trace_seed_replay_lowprob_success_retention`
- train 40M more steps, reaching a 60M-level v19 decision
- evaluate every 5M milestone; do not assume the final checkpoint is best
- do not edit `config/level3_dr.toml`

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --allow-step-curve-maturation \
  --structural-hypothesis v19_trace_seed_replay_lowprob_success_retention_maturation_from_loop074_20m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop074_continue_v19_lowprob_replay_to_60m.md
```

Run the same command with `--dry-run` first.

## Rollback Rule

Reject this maturation if no milestone beats either:

- success rate above 0.20, or
- mean gates above 1.60,

or if crash rises above 0.80 without compensating success/gate progress.

Prefer any milestone that recovers loop071's diagnostic frontier of 0.25
success or 2.00 mean gates without a crash increase. If it reaches 0.25 success
or 2.00 mean gates but remains slow, continue the same hypothesis toward a 90M
confirmation before changing reward numbers.
