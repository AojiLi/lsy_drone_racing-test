# V27 Retention Dataset Audit

- Created at: 2026-06-23T17:21:25+00:00
- Dataset: `experiments/level3_ppo_loop/retention_datasets/v46_loop107_loop101_loop110_frontier_success_union_v5.npz`
- Validation status: `passed`
- Samples: 24388
- Successful train-pool episodes: 72
- Excluded seed overlap: []
- Student obs dim: 68
- Samples by target gate: `{'0': 4815, '1': 6405, '2': 6938, '3': 6230}`

## Checkpoint Retention

| Checkpoint | Agreement | Episode min | Episodes >=0.80 | KL | Action MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop110_v39_3m | 0.830296 | 0.658113 | 36/72 | 0.083788 | 0.017196 |

## Notes

- This is an offline teacher-success retention audit, not Level3 hard eval.
- It does not inspect `final_locked` seeds.
- Hard acceptance still requires unchanged `config/level3.toml` evaluator metrics.
