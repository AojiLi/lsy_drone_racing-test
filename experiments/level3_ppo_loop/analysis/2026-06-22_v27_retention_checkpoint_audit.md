# V27 Retention Dataset Audit

- Created at: 2026-06-22T12:01:03+00:00
- Dataset: `experiments/level3_ppo_loop/retention_datasets/v27_loop052_train_pool_success_v5_teacher_v8_student.npz`
- Validation status: `passed`
- Samples: 2681
- Successful train-pool episodes: 8
- Excluded seed overlap: []
- Student obs dim: 82
- Samples by target gate: `{'0': 492, '1': 700, '2': 751, '3': 738}`

## Checkpoint Retention

| Checkpoint | Agreement | Episode min | Episodes >=0.80 | KL | Action MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop078_final | 0.569564 | 0.525469 | 0/8 | 2.210634 | 0.162188 |
| loop085_3M | 0.545226 | 0.496649 | 0/8 | 2.427917 | 0.152607 |
| loop086_1M | 0.684166 | 0.651475 | 0/8 | 1.994774 | 0.109304 |
| loop087_final | 0.836255 | 0.789199 | 7/8 | 1.418371 | 0.01754 |

## Notes

- This is an offline teacher-success retention audit, not Level3 hard eval.
- It does not inspect `final_locked` seeds.
- Hard acceptance still requires `config/level3_dr.toml` evaluator metrics.
