# Main-Agent Decision After loop031

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Named next lane:

`v5_curriculum_gate_obstacle_staged_training`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- A training-only curriculum config may be proposed only as an explicit
  structural lane and must still hard-evaluate checkpoints on
  `config/level3_dr.toml`.
- Do not continue `level3_loop_031_v5_legacy_centerline_safety_recovery_from_loop020_25m_30m`
  unchanged.

## Evidence

Latest analyzed trial:

- Trial: `level3_loop_031_v5_legacy_centerline_safety_recovery_from_loop020_25m_30m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_031_v5_legacy_centerline_safety_recovery_from_loop020_25m_30m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_031_v5_legacy_centerline_safety_recovery_from_loop020_25m_30m`

Best loop031 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_031_v5_legacy_centerline_safety_recovery_from_loop020_25m_30m/level3_loop_031_v5_legacy_centerline_safety_recovery_from_loop020_25m_30m_step_025000000.ckpt`
- Success rate: `0.05`
- Mean successful time: `6.18s`
- Crash rate: `0.95`
- Mean gates: `1.10`

Current global best remains:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

## Reviewer Synthesis

Evaluator metrics:

- Reject continuing loop031 unchanged.
- loop031 started from the loop020 global-best checkpoint and regressed in
  success, crash rate, and mean gates.
- Hard-eval evidence alone does not prove the exact next lever.

W&B/PPO diagnostics:

- Training signal did not convert into hard-eval progress.
- `passed_gate_rate` stayed flat, `finished_rate` stayed at zero in the tail,
  and event rewards weakened.
- PPO did not show a classic blow-up, but policy updates look weak or
  ineffective: low KL, near-zero clip fraction, tiny policy loss, and high
  entropy.

Structure/research synthesis:

- loop031 reduces confidence in more legacy/gate-potential reward-number
  tweaks.
- v5 local-obstacle observation is not rejected; it still has the strongest
  local and remote support.
- The next structural hypothesis should target the gate-traversal versus
  obstacle-avoidance conflict with staged/curriculum training while preserving
  hard eval on the real Level3 track.

## Next Action

Before launching training, define and dry-run the named structural lane
`v5_curriculum_gate_obstacle_staged_training`.

Minimum requirements:

- Use W&B project `ADR-PPO-Racing-Level3`.
- Use exactly one train/evaluate chunk with `--max-iterations 1`.
- Attach this packet with `--approved-hypothesis-packet`.
- Attach the loop031 analysis packet with `--analysis-packet`.
- If a training-only curriculum config is used, record it as training config
  only and keep `--eval-config level3_dr.toml`.
- Use milestone checkpoint evaluation and run
  `scripts/analyze_level3_ppo_trial.py` immediately after the chunk.
- Use exactly three post-run reviewers: evaluator metrics, W&B/PPO diagnostics,
  and structure/research synthesis.

Promotion criteria:

- Any checkpoint improves over loop020 on success rate (`>0.15`), or
- any checkpoint improves mean gates above `1.45`, or
- same success with materially lower crash/tilt.

Rollback criteria:

- Best success remains `<=0.05`, or
- mean gates stay below `1.15`, or
- W&B pass/finish conversion remains flat, or
- the lane requires changing the Level3 hard-eval track.
