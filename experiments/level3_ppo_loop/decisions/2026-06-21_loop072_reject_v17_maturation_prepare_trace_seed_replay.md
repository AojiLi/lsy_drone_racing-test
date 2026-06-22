# Loop072 Decision: Reject V17 Maturation, Launch Trace-Seed Replay Lane

Decision: launch_named_structural_lane

Pending gate resolved:

- trial_id: `level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m_analysis.json`

## Verdict

Reject v17 trace-mixed corridor maturation. Do not continue v17 to 90M.

Best loop072 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m_step_020000000.ckpt`

Metrics on hard eval `config/level3_dr.toml`:

- success rate: 0.20
- mean successful time: 8.165s
- crash rate: 0.80
- mean gates: 1.60
- target met: false

Loop072 failed the loop071 continuation test:

- loop071 20M: 0.25 success, 2.00 mean gates, 0.75 crash, 8.524s
- loop072 20M: 0.20 success, 1.60 mean gates, 0.80 crash, 8.165s
- loop072 later milestones regressed to 0.10 success and 0.90 crash

The global best remains loop069 25M:

`lsy_drone_racing/control/checkpoints/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt`

Metrics:

- success rate: 0.20
- mean successful time: 6.675s
- crash rate: 0.80
- mean gates: 1.45

Loop072 tied loop069 on success and crash, slightly improved mean gates, but
was much slower. It is not a promotion checkpoint.

## Subagent Consensus

- evaluator metrics: reject loop072 maturation, do not promote any loop072
  checkpoint, keep loop069 as global best.
- W&B/PPO diagnostics: PPO was stable, but train reward and gate proxies did
  not convert into hard-eval progress. Do not add time pressure now.
- structure/research synthesis: do not continue v17 and do not do a standalone
  reward retune. If training resumes, launch a new named structural lane:
  `v18_trace_seed_replay_default_retention_from_loop069_25m`.

## Next Direction

Launch a runnable named structural lane:

`v18_trace_seed_replay_default_retention_from_loop069_25m`

Contract:

- start from loop069 25M checkpoint
- keep v5 local-obstacle observation
- keep 2x256 MLP actor/critic
- keep loop052 nominal reward numbers
- keep training config `level3_dr.toml`
- keep hard eval `config/level3_dr.toml`
- use a training-only targeted hard-seed geometry-replay sampler with
  default-distribution retention:
  - `track_generator_profile=trace_seed_replay_default_retention`
  - `replay_seed_probability=0.25`
  - `replay_seeds=[2, 3, 5, 7, 9, 14, 15, 17, 18, 20]`
- do not edit `config/level3_dr.toml`

This lane has explicit orchestrator support through:

`v18_trace_seed_replay_default_retention_from_loop069_25m`

It still requires a dry-run before launch.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v18_trace_seed_replay_default_retention_from_loop069_25m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop072_reject_v17_maturation_prepare_trace_seed_replay.md
```

## Rollback Rule For V18

Reject v18 if it does not beat 0.20 success or 1.45 mean gates with crash no
worse than 0.80. Prefer recovery of loop071's diagnostic frontier of 0.25
success and 2.00 mean gates without worsening time.
