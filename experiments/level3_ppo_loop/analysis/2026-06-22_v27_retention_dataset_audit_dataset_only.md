# V27 Retention Dataset Audit

- Created at: 2026-06-22T12:00:49+00:00
- Dataset: `experiments/level3_ppo_loop/retention_datasets/v27_loop052_train_pool_success_v5_teacher_v8_student.npz`
- Validation status: `passed`
- Samples: 2681
- Successful train-pool episodes: 8
- Excluded seed overlap: []
- Student obs dim: 82
- Samples by target gate: `{'0': 492, '1': 700, '2': 751, '3': 738}`

## Checkpoint Retention

- No checkpoints were audited.

## Notes

- This is an offline teacher-success retention audit, not Level3 hard eval.
- It does not inspect `final_locked` seeds.
- Hard acceptance still requires `config/level3_dr.toml` evaluator metrics.
