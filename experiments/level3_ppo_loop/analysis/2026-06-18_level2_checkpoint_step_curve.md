# Level2 Checkpoint Step Curve Review

Date: 2026-06-18

Purpose: use successful Level2 PPO checkpoint curves to calibrate Level3 train/eval
chunk size and checkpoint-selection strategy. Level3 training may use curricula, but
the acceptance gate remains `config/level3_dr.toml`.

## Source Controller

`lsy_drone_racing/control/ppo_level2_inference.py` currently selects:

```text
checkpoints/level2_DR_latencyobs_middlemanuever/level2_DR_latencyobs_middlemanuever_final.ckpt
```

The same file lists `level2_DR_latencyobs_middlemanuever_onemoretime_final.ckpt`
as a faster, more aggressive backup.

## Evaluation Commands

```bash
pixi run -e gpu python scripts/compare_level2_ppo_checkpoints.py \
  --checkpoint-dir lsy_drone_racing/control/checkpoints/level2_DR_latencyobs_middlemanuever \
  --config level2_dr.toml \
  --seed-start 1 \
  --num-seeds 100 \
  --min-step 60000000 \
  --out-prefix experiments/level3_ppo_loop/level2_middlemanuever_60plus_100seed
```

```bash
pixi run -e gpu python scripts/compare_level2_ppo_checkpoints.py \
  --checkpoint-dir lsy_drone_racing/control/checkpoints/level2_DR_latencyobs_middlemanuever_onemoretime \
  --config level2_dr.toml \
  --seed-start 1 \
  --num-seeds 100 \
  --only-steps-m 30,60,100,120,140,145 \
  --include-final \
  --out-prefix experiments/level3_ppo_loop/level2_onemoretime_key_100seed
```

The first full 5M-55M scan was interrupted after printing results, so those
early points are recorded here from stdout rather than a CSV artifact.

## Balanced Middlemanuever Curve

| Checkpoint | Success | Mean success time | Mean gates | Notes |
|---:|---:|---:|---:|---|
| 5M | 0% | n/a | 0.51 | no completion |
| 10M | 0% | n/a | 0.84 | no completion |
| 15M | 0% | n/a | 1.52 | gate acquisition starts |
| 20M | 0% | n/a | 1.59 | no completion |
| 25M | 0% | n/a | 2.37 | partial track |
| 30M | 0% | n/a | 2.69 | still no success |
| 35M | 0% | n/a | 2.25 | regression |
| 40M | 0% | n/a | 2.51 | still no success |
| 45M | 43% | 7.27s | 3.20 | first useful success jump |
| 50M | 47% | 6.39s | 3.09 | faster |
| 55M | 52% | 6.42s | 3.13 | near 60% |
| 60M | 53% | 6.44s | 3.25 | CSV-backed |
| 65M | 58% | 6.27s | 3.32 | near target |
| 70M | 66% | 6.20s | 3.34 | first >=60% checkpoint |
| 75M | 63% | 5.79s | 3.30 | faster, success dips |
| 80M | 69% | 5.90s | 3.34 | stronger |
| 85M | 68% | 5.89s | 3.23 | plateau/noise |
| 90M | 72% | 5.91s | 3.39 | stronger |
| 95M | 77% | 5.82s | 3.50 | best scanned step |
| final | 72% | 5.89s | 3.25 | final below 95M |

CSV artifacts:

- `experiments/level3_ppo_loop/level2_middlemanuever_60plus_100seed_summary.csv`
- `experiments/level3_ppo_loop/level2_middlemanuever_60plus_100seed_episodes.csv`

## Onemoretime Key Curve

| Checkpoint | Success | Mean success time | Mean gates | cmd tilt >30deg |
|---:|---:|---:|---:|---:|
| 30M | 2% | 20.42s | 2.46 | 8.69% |
| 60M | 75% | 5.92s | 3.47 | 29.24% |
| 100M | 75% | 5.76s | 3.43 | 35.46% |
| 120M | 70% | 5.58s | 3.20 | 38.47% |
| 140M | 70% | 5.34s | 3.20 | 41.20% |
| 145M | 75% | 5.53s | 3.38 | 39.09% |
| final | 80% | 5.50s | 3.49 | 38.91% |

CSV artifacts:

- `experiments/level3_ppo_loop/level2_onemoretime_key_100seed_summary.csv`
- `experiments/level3_ppo_loop/level2_onemoretime_key_100seed_episodes.csv`

## Implications For Level3

1. A 30M from-scratch chunk is too short to judge final viability by success rate.
   In Level2, 30M was still 0%-2% success.
2. 30M can still be useful as a diagnostic chunk, but the primary signal should
   be gates reached, crash type, W&B reward-component conversion, and PPO health.
3. For a promising from-scratch Level3 branch, the first serious success-rate
   decision should be at 60M-90M, not 30M.
4. Keep evaluating intermediate checkpoints. Level2 `middlemanuever` peaked at
   95M while final regressed; final-only selection would have missed the better
   checkpoint.
5. Longer training can trade success/safety for speed. The onemoretime branch
   reached 80% at final, but cmd tilt >30deg was much higher than the balanced
   branch.
6. For Level3, use 5M or 10M checkpoint intervals inside longer chunks, then
   select by hard `level3_dr.toml` eval rather than by final checkpoint.

Recommended Level3 loop adjustment:

- Use 30M only for cheap screening and debugging.
- For any branch that improves mean gates or produces non-zero success, extend
  on the same hypothesis to at least 60M and often 90M before rejecting it.
- Use 20-seed/6-checkpoint quick eval during search, then 100-seed hard eval
  for candidate checkpoints.
- Do not rely on training reward alone and do not rely on final checkpoints.
