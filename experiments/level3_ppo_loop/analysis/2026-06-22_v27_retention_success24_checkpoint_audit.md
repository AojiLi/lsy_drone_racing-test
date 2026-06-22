# V27 Retention Dataset Audit

- Created at: 2026-06-22T12:03:39+00:00
- Dataset: `experiments/level3_ppo_loop/retention_datasets/v27_loop052_train_pool_success24_v5_teacher_v8_student.npz`
- Validation status: `passed`
- Samples: 8246
- Successful train-pool episodes: 24
- Excluded seed overlap: []
- Student obs dim: 82
- Samples by target gate: `{'0': 1557, '1': 2209, '2': 2321, '3': 2159}`

## Checkpoint Retention

| Checkpoint | Agreement | Episode min | Episodes >=0.80 | KL | Action MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop078_final | 0.550903 | 0.46519 | 0/24 | 2.215033 | 0.176571 |
| loop085_3M | 0.515735 | 0.463315 | 0/24 | 2.440363 | 0.169583 |
| loop086_1M | 0.644707 | 0.597826 | 0/24 | 2.013986 | 0.128425 |
| loop087_final | 0.804208 | 0.726277 | 11/24 | 1.430471 | 0.025307 |

## Notes

- This is an offline teacher-success retention audit, not Level3 hard eval.
- It does not inspect `final_locked` seeds.
- Hard acceptance still requires `config/level3_dr.toml` evaluator metrics.
