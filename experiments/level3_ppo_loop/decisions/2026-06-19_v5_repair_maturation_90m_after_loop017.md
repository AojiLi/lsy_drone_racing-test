# Level3 Decision: Mature V5 Repair To 90M After Loop 017

Date: 2026-06-19

## Trial

- Trial id: `level3_loop_017_v5_gate_acquisition_repair_mature_60m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_017_v5_gate_acquisition_repair_mature_60m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_017_v5_gate_acquisition_repair_mature_60m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_017_v5_gate_acquisition_repair_mature_60m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_017_v5_gate_acquisition_repair_mature_60m/level3_loop_017_v5_gate_acquisition_repair_mature_60m_final.ckpt`
- Hard-eval success rate: `0.05`
- Mean successful time: `5.26s`
- Crash rate: `0.95`
- Timeout rate: `0.00`
- Mean gates: `0.95`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Loop 017 does not meet the target, but it ties the
  standing global best on success, crash, and mean gates while improving the
  single successful time from `6.10s` to `5.26s`. It also improves over loop016
  v5 on mean gates (`0.65` to `0.95`). The branch narrowly qualifies for 90M
  maturation because it has non-zero hard-eval success and meaningful gate
  progress.
- `wandb_ppo_diagnostics`: PPO stability is acceptable. Approx KL and clipfrac
  are not showing destructive updates, entropy is healthy, and explained
  variance remains usable despite high value loss. W&B conversion is partial:
  reward and gate signals improved mean gates and successful time, but not
  success rate or crash rate. Continue the same hypothesis once more rather
  than silently tuning PPO or changing structure.
- `structure_research_synthesis`: Remote v5 evidence supports patience at
  longer horizons. Local loop017 is comparable to the remote v5 early hard-eval
  point and is cleaner than the old original-observation best. All-gates/v4
  remains rejected, and changing reward/training numbers now would blur the
  90M confirmation test.

## Main-Agent Decision

Selected decision: `continue_same_hypothesis`

Continue the repaired v5 local-obstacle branch unchanged from the loop017 final
checkpoint to the 90M evidence point. This is not a new structural lane, not a
reward retune, and not a PPO hyperparameter change.

## Rationale

- Hard-eval evidence: loop017 remains far from target (`5%` success vs `60%`
  required), but it reaches `0.95` mean gates and ties the old best success
  while improving successful time.
- Step-curve evidence: the prior promotion rule approved 90M continuation if
  60M reached at least `0.90` mean gates without crash worse than `95%`.
  Loop017 satisfies that exact condition.
- W&B evidence: training reward and gate signals improved without PPO collapse,
  but finish/crash conversion remains weak. The next hard-eval result should
  decide whether unchanged v5 maturation has run out of useful signal.
- Structural evidence: v5 remains the only source-backed local-obstacle
  observation lane. Do not restore all-gates/v4 and do not modify the Level3
  track.
- Boundary: final acceptance remains hard eval on `config/level3_dr.toml`.

## Approved Next Experiment

Name: `v5_gate_acquisition_repair_mature_90m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_017_v5_gate_acquisition_repair_mature_60m/level3_loop_017_v5_gate_acquisition_repair_mature_60m_final.ckpt
```

Observation layout:

```text
level3_target_gate_nearest_gate_2obs_local_history_v5
```

Keep the loop017 reward and training numbers unchanged.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name v5_gate_acquisition_repair_mature_90m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_017_v5_gate_acquisition_repair_mature_60m/level3_loop_017_v5_gate_acquisition_repair_mature_60m_final.ckpt \
  --train-timesteps 90000000 \
  --checkpoint-interval 5000000 \
  --allow-step-curve-maturation \
  --keep-latest-params \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_017_v5_gate_acquisition_repair_mature_60m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-19_v5_repair_maturation_90m_after_loop017.md
```

## Promotion And Rollback

- Promote to wider-seed confirmation or longer continuation only if a 90M
  checkpoint improves success beyond `5%` or clearly improves mean gates while
  reducing crash below `95%`.
- If 90M remains at `5%` success and `95%` crash with no evaluator conversion,
  stop unchanged v5 maturation and require `change_reward_or_training_numbers`
  or a new named structural/training lane.
