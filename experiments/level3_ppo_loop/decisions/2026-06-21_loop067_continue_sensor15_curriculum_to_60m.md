# Loop067 Decision: Continue Sensor15 Curriculum To 60M

## Decision

`continue_same_hypothesis`

Continue:

`v15_sensor15_curriculum_maturation_from_loop067_10m`

This packet resolves the post-run decision gate for:

- trial_id:
  `level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m_analysis.json`

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 target track geometry, gate layout, obstacle layout, or
  randomization.
- Continue only through the named training-only sensor15 curriculum lane.

## Evidence

Loop067 tested:

`v15_loop052_sensor15_curriculum_nominal_reward`

The best hard-eval checkpoint inside loop067 was the 10M checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m/level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m_step_010000000.ckpt`

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| loop052 final | 0.20 | 1.40 | 0.80 | 6.975s |
| loop067 10M | 0.20 | 1.60 | 0.80 | 7.445s |
| loop067 final | 0.05 | 1.05 | 0.95 | 6.040s |

Loop067 does not replace loop052 as global best because its successful time is
slower and above the 7.0s target. It does satisfy the v15 promotion rule
because mean gates improved from 1.40 to 1.60 without worsening success or
crash at the selected 10M checkpoint.

## Subagent Synthesis

Evaluator metrics:

- Continue v15 to a 60M-level maturation chunk.
- Use intermediate checkpoint selection; do not trust loop067 final.
- The 10M checkpoint satisfies the promotion rule through `mean_gates > 1.45`.

W&B/PPO diagnostics:

- PPO is not obviously unstable.
- `learning_rate=5e-5` and `anneal_lr=False` were active.
- KL and clip fraction are low/flat; entropy does not collapse.
- Race conversion is partial and noisy, so continue only one maturation chunk
  before deciding again.

Structure/research synthesis:

- v15 is structurally distinct from loop032/no-wrapper curriculum because it
  keeps train robustness wrappers and only increases training sensor visibility.
- Continue from loop067 10M, not loop067 final.
- Do not apply the analyzer's generic gate-acquisition reward bump yet; v13/v14
  already weakened the case for immediate reward-number churn.

## Continuation Contract

Name:

`v15_sensor15_curriculum_maturation_from_loop067_10m`

Run proposal:

`structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m/level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m_step_010000000.ckpt`

Training config:

`config/level3_dr_stage2_gate0_sensor15.toml`

Hard eval config:

`config/level3_dr.toml`

Keep fixed:

- v5 local-obstacle observation;
- 2x256 Tanh MLP Actor/Critic;
- loop052 nominal reward numbers;
- `learning_rate=5e-5`;
- `anneal_lr=False`;
- 5M checkpoint interval;
- W&B online logging.

Training horizon:

- 50M continuation from the 10M checkpoint, giving a 60M-level maturation
  decision point for this lane.
- Use `--allow-step-curve-maturation`.
- Use milestone-aware hard eval and do not assume the final checkpoint is best.

## Promotion Rule

Continue toward 90M only if the 60M-level review finds a checkpoint with:

- `success_rate > 0.20`, or
- `mean_gates > 1.60` with `crash_rate <= 0.80`, or
- `success_rate == 0.20` with faster successful time than 7.445s and W&B
  pass/finish/plane-cross conversion improving.

## Rejection Rule

Reject or change lane if no checkpoint beats loop067 10M, especially if:

- best success stays `<= 0.20`,
- mean gates stay `<= 1.60`,
- crash rises above `0.80`,
- W&B pass/finish/plane-cross conversion remains flat.

The next structural fallback after rejection should be a targeted seed/geometry
sampler curriculum, not another broad no-wrapper curriculum and not an
unexplained reward-only repeat.

## Required Post-Run Work

After the train/evaluate chunk:

1. Run `scripts/analyze_level3_ppo_trial.py`.
2. Use exactly three review roles: evaluator metrics, W&B/PPO diagnostics, and
   structure/research synthesis.
3. Write a new main-agent decision packet before launching another training
   chunk.
