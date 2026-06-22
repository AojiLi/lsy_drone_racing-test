# Loop073 Decision: Reject V18, Launch Low-Probability Replay With Success Retention

Decision: launch_named_structural_lane

Pending gate resolved:

- trial_id: `level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m_analysis.json`

## Verdict

Reject v18 seed replay as run. Do not continue it unchanged to 60M.

Best loop073 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m_step_025000000.ckpt`

Metrics on hard eval `config/level3_dr.toml`:

- success rate: 0.15
- mean successful time: 7.467s
- crash rate: 0.85
- mean gates: 1.60
- target met: false

Loop073 failed the v18 rollback bar:

- loop069 25M: 0.20 success, 1.45 mean gates, 0.80 crash, 6.675s
- loop071 20M: 0.25 success, 2.00 mean gates, 0.75 crash, 8.524s
- loop073 25M: 0.15 success, 1.60 mean gates, 0.85 crash, 7.467s

The global best remains loop069 25M.

## Subagent Consensus

- evaluator metrics: reject v18. The targeted replay seeds only reached 1/10
  success, while non-replay seeds also regressed. Do not promote loop073.
- W&B/PPO diagnostics: PPO was stable and reward proxies improved cosmetically,
  but hard-eval conversion failed. Do not tune optimizer, broad rewards, or time
  pressure from this evidence.
- structure/research synthesis: the seed-replay axis has a partial signal, but
  v18's 25% replay over hard seeds was too interference-heavy. Launch a lower
  replay-probability lane that retains known success seeds.

## Next Lane

Launch named structural lane:

`v19_trace_seed_replay_lowprob_success_retention_from_loop069_25m`

Contract:

- start from loop069 25M checkpoint
- keep v5 local-obstacle observation
- keep 2x256 MLP actor/critic
- keep loop052 nominal reward numbers
- keep constant learning rate 5e-5
- keep training config `level3_dr.toml`
- keep hard eval `config/level3_dr.toml`
- use training-only `track_generator_profile=trace_seed_replay_lowprob_success_retention`
- use `replay_seed_probability=0.12`
- replay seeds: `[1, 4, 9, 11, 12, 16, 17, 18, 20]`
- do not edit `config/level3_dr.toml`

The seed set balances:

- loop069 retention successes: `1, 11, 12, 16`
- v17/v18 frontier successes: `4, 9`
- hard-progress seeds: `17, 18, 20`

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v19_trace_seed_replay_lowprob_success_retention_from_loop069_25m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop073_reject_v18_launch_lowprob_replay_success_retention.md
```

## Rollback Rule

Reject v19 if it does not restore at least 0.20 success with crash <= 0.80
while preserving replay-seed gate progress. Prefer any milestone that recovers
loop071's diagnostic frontier of 0.25 success or 2.00 mean gates without a
crash increase.
