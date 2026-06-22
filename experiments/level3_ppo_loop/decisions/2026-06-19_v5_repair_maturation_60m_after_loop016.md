# Level3 Decision: Mature V5 Repair To 60M After Loop 016

Date: 2026-06-19

## Trial

- Trial id: `level3_loop_016_v5_gate_acquisition_repair_30m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_016_v5_gate_acquisition_repair_30m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_016_v5_gate_acquisition_repair_30m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_016_v5_gate_acquisition_repair_30m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_016_v5_gate_acquisition_repair_30m/level3_loop_016_v5_gate_acquisition_repair_30m_final.ckpt`
- Hard-eval success rate: `0.05`
- Mean successful time: `5.88s`
- Crash rate: `0.95`
- Mean gates: `0.65`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Loop 016 ties the standing global best on success
  (`5%`) and crash (`95%`), is faster on its single success (`5.88s`), and is
  much cleaner in tilt. It trails the standing best on mean gates (`0.65` vs
  `0.95`) but qualifies for maturation because success is non-zero.
- `wandb_ppo_diagnostics`: PPO is stable enough to continue. Reward and gate
  proxies improved, but conversion is still weak and crash remains dominant.
  Do not tune PPO hyperparameters yet; keep the checkpoint explicit to avoid
  falling back to the incompatible original-observation global best.
- `structure_research_synthesis`: Remote v5 evidence improves only at longer
  horizons. Loop 016 should be matured unchanged to the 60M evidence point
  before replacing v5 or changing reward numbers again.

## Main-Agent Decision

Selected decision: `continue_same_hypothesis`

Continue the repaired v5 branch unchanged from the loop016 final checkpoint.
This is not a new structural lane and not a reward retune.

## Rationale

- Local evaluator evidence: loop016 improved the v5 lane from `0%` success and
  `0.40` mean gates to `5%` success and `0.65` mean gates.
- Step-curve evidence: the branch satisfies the loop's promotion rule because
  it has non-zero hard-eval success. A promising 30M branch should mature to
  60M before being rejected.
- W&B evidence: reward improved and gate proxies appeared, but finish/crash
  conversion is still weak. Longer training is justified before another
  parameter change.
- Structural evidence: v5 remains the source-backed observation lane; all-gates
  v4 remains rejected.
- Boundary: do not modify Level3 track geometry or randomization. Final
  acceptance remains hard eval on `config/level3_dr.toml`.

## Approved Next Experiment

Name: `v5_gate_acquisition_repair_mature_60m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_016_v5_gate_acquisition_repair_30m/level3_loop_016_v5_gate_acquisition_repair_30m_final.ckpt
```

Observation layout:

```text
level3_target_gate_nearest_gate_2obs_local_history_v5
```

Keep the loop016 reward/training numbers unchanged.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name v5_gate_acquisition_repair_mature_60m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_016_v5_gate_acquisition_repair_30m/level3_loop_016_v5_gate_acquisition_repair_30m_final.ckpt \
  --train-timesteps 60000000 \
  --checkpoint-interval 5000000 \
  --allow-step-curve-maturation \
  --keep-latest-params \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_016_v5_gate_acquisition_repair_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-19_v5_repair_maturation_60m_after_loop016.md
```

## Promotion And Rollback

- Promote toward 90M if a checkpoint improves beyond `5%` success or reaches at
  least `0.90` mean gates without crash worse than `95%`.
- If 60M loses non-zero success and remains below `0.75` mean gates, stop
  unchanged v5 maturation and require a new named structural lane or research
  packet.
