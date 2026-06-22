# Loop087 Decision: Hold V27 Teacher KL Sweep

Decision: hold_for_more_analysis

Pending gate resolved for:

- trial_id:
  `level3_loop_087_structural_v27_teacher_retention_beta010_5m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_087_structural_v27_teacher_retention_beta010_5m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_087_structural_v27_teacher_retention_beta010_5m_analysis.json`

## Verdict

Hold the v27 teacher-retention KL beta sweep.

Do not launch another beta arm, do not mature beta=0.10 to 60M/90M, and do not
follow the analyzer's generic gate-reward retune command as the immediate next
training step.

## Hard-Eval Evidence

Loop087 beta=0.10 validation best, final checkpoint:

- success: 0.17
- crash: 0.83
- mean gates: 1.50
- mean successful time: 6.991s
- success CI95: [0.109, 0.255]
- endpoint classes: `{"bounds_or_ground": 83, "success": 17}`

Loop087 3M validation:

- success: 0.16
- crash: 0.84
- mean gates: 1.49
- mean successful time: 6.944s

Loop052 validation anchor:

- success: 0.20
- crash: 0.80
- mean gates: 1.47
- mean successful time: 6.858s

Loop087 improved over the earlier v27 arms but did not restore or exceed the
loop052 anchor:

| Arm | Best validation success | Crash | Mean gates |
| --- | ---: | ---: | ---: |
| beta=0 | 0.10 | 0.90 | 1.38 |
| beta=0.03 | 0.14 | 0.86 | 1.55 |
| beta=0.10 | 0.17 | 0.83 | 1.50 |
| loop052 anchor | 0.20 | 0.80 | 1.47 |

## Retention and PPO Evidence

The v27 teacher-retention path is real and healthy:

- `retention/sampled_batch_size`: 512 throughout
- `losses/teacher_kl`: 2.1588 -> 1.4206
- `losses/teacher_action_mse`: 0.1459 -> 0.0182
- `retention/teacher_agreement`: 0.6189 -> 0.8351

PPO does not look unstable:

- `approx_kl` remained far below `target_kl=0.03`
- `clipfrac` stayed low
- entropy decayed mildly
- explained variance stayed usable
- value loss did not explode

The failure is therefore not an empty-KL implementation bug and not obvious PPO
instability. It is a conversion failure: teacher-retention and training proxies
improve, but hard Level3 reliability does not exceed the anchor.

## Subagent Synthesis

Evaluator metrics:

- beta=0.10 improved over beta=0 and beta=0.03;
- beta=0.10 did not exceed loop052 success or crash;
- failures remain dominated by `bounds_or_ground`.

W&B/PPO diagnostics:

- teacher-retention metrics are valid and healthy;
- PPO metrics are stable;
- W&B improvements do not convert into hard-eval reliability.

Structure/research:

- the v27 three-arm screen is exhausted;
- the loop086 stop rule applies;
- the next move should be data/implementation audit, not more v27 beta sweep.

## Approved Next Work

Hold training and improve the v27 evidence/data path before launching any new
structural run. The next work packet should cover:

1. Validate the retention dataset metadata and seed exclusion.
2. Add analyzer summaries for v27 retention metrics.
3. Add an episode-level teacher-retention evaluation.
4. Build a larger or stratified train-pool retention/failure-correction dataset.
5. Keep the hard eval on unchanged `config/level3_dr.toml`.
6. Do not inspect or use `final_locked` seeds.

Suggested future lane name after the audit:

`v27_stratified_retention_failure_correction_data_audit`

## Rejected Actions

- continue beta=0.10;
- try beta > 0.10;
- mature v27 beta=0.10 to 60M or 90M;
- launch another training chunk without a new decision packet;
- follow the analyzer's generic reward scaling command immediately;
- modify `config/level3_dr.toml`;
- inspect or train on final_locked seeds.
