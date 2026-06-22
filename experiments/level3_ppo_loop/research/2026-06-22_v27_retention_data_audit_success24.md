# V27 Retention Data Audit: Success24 Expansion

Status: audit packet. Do not launch training from this packet alone.

## Scope

This audit follows the loop087 hold decision:

`experiments/level3_ppo_loop/decisions/2026-06-22_loop087_hold_v27_teacher_kl_for_data_audit.md`

It does not modify `config/level3_dr.toml`, does not inspect `final_locked`
seeds, and does not run a new training chunk.

## Dataset Validation

Original v27 retention dataset:

- path:
  `experiments/level3_ppo_loop/retention_datasets/v27_loop052_train_pool_success_v5_teacher_v8_student.npz`
- samples: 2681
- successful train-pool episodes: 8
- excluded seed overlap: none
- student observation dim: 82
- target gate sample counts: gate0 492, gate1 700, gate2 751, gate3 738
- audit report:
  `experiments/level3_ppo_loop/analysis/2026-06-22_v27_retention_checkpoint_audit.md`

Expanded success24 dataset:

- path:
  `experiments/level3_ppo_loop/retention_datasets/v27_loop052_train_pool_success24_v5_teacher_v8_student.npz`
- samples: 8246
- successful train-pool episodes: 24
- excluded seed overlap: none
- student observation dim: 82
- target gate sample counts: gate0 1557, gate1 2209, gate2 2321, gate3 2159
- audit report:
  `experiments/level3_ppo_loop/analysis/2026-06-22_v27_retention_success24_checkpoint_audit.md`

Both datasets are train-pool only and exclude:

- `dev_seen`: 1-20
- `validation_unseen`: 101-200
- `final_locked`: 1001-1200

## Episode-Level Retention Findings

Offline teacher-success retention audit on the original 8-episode dataset:

| Checkpoint | Agreement | Episode min | Episodes >=0.80 | KL | Action MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop078 final | 0.569564 | 0.525469 | 0/8 | 2.210634 | 0.162188 |
| loop085 beta=0 3M | 0.545226 | 0.496649 | 0/8 | 2.427917 | 0.152607 |
| loop086 beta=0.03 1M | 0.684166 | 0.651475 | 0/8 | 1.994774 | 0.109304 |
| loop087 beta=0.10 final | 0.836255 | 0.789199 | 7/8 | 1.418371 | 0.017540 |

Offline teacher-success retention audit on the expanded 24-episode dataset:

| Checkpoint | Agreement | Episode min | Episodes >=0.80 | KL | Action MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop078 final | 0.550903 | 0.465190 | 0/24 | 2.215033 | 0.176571 |
| loop085 beta=0 3M | 0.515735 | 0.463315 | 0/24 | 2.440363 | 0.169583 |
| loop086 beta=0.03 1M | 0.644707 | 0.597826 | 0/24 | 2.013986 | 0.128425 |
| loop087 beta=0.10 final | 0.804208 | 0.726277 | 11/24 | 1.430471 | 0.025307 |

## Interpretation

The v27 teacher-retention implementation is real: beta=0.10 improves
teacher-action agreement sharply over beta=0 and beta=0.03.

The original 8-episode retention dataset was too narrow to prove robust
teacher-success retention. Loop087 clears the 0.80 agreement proxy on the
original dataset, but on the broader success24 dataset it only reaches 11/24
episodes above 0.80 and has a minimum episode agreement of 0.726.

This explains why W&B retention curves looked healthy while validation hard
eval stayed below the loop052 anchor. The model can retain the narrow retained
set, but it has not robustly retained teacher-success behavior across a broader
train-pool success distribution, and it still lacks a failure-correction data
path for the dominant `bounds_or_ground` validation failures.

## Recommended Next Work

Do not continue the old v27 beta sweep.

Before any next training chunk, prepare a named data/structure lane that uses:

1. the expanded success24 retention dataset or a larger successor;
2. an explicit failure-correction data collection path from train_pool seeds,
   classified by geometry rather than validation seed id;
3. analyzer retention summaries, which are now implemented;
4. episode-level retention audit as a required pre-launch artifact;
5. hard eval only on unchanged `config/level3_dr.toml`;
6. no `final_locked` seed inspection.

Candidate lane name:

`v28_success24_retention_failure_correction_data_lane`

This packet is evidence for designing that lane. It is not, by itself, approval
to launch training.
