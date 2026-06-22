# Level3 Decision: V5 Action Envelope 75deg After Loop 023

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_023_v5_action_envelope_60deg_from_loop020_25m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m_final.ckpt`
- Hard-eval success rate: `0.05`
- Mean successful time: `6.02s`
- Crash rate: `0.95`
- Mean gates: `1.10`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Do not mature the 60-degree lane. It reduced command
  tilt but did not improve task progress: `5%` success, `95%` crash, and `1.10`
  mean gates versus loop020's `15%`, `85%`, and `1.45`.
- `wandb_ppo_diagnostics`: The 60-degree envelope did not solve conversion.
  PPO metrics remain stable, but hard-eval performance worsened versus loop020.
  The next action should be a structural/controller lane rather than more
  safety reward tuning.
- `structure_research_synthesis`: Reject 60 degrees as likely over-constrained.
  Test a less restrictive `75deg` matched action envelope from loop020 25M
  before moving to gate-acquisition reward rebalance.

## Main-Agent Decision

Selected decision: `launch_named_structural_lane`

Reject `v5_localobs_action_envelope_60deg` and launch
`v5_localobs_action_envelope_75deg`. Keep the Level3 track immutable, keep hard
eval on `config/level3_dr.toml`, keep v5 local-obstacle observation, keep PPO
hyperparameters unchanged, and keep the loop020 completion-backloaded reward
family unchanged. The only structural change for this lane is
`action_rp_limit_deg=75.0`.

## Rationale

- Local evaluator evidence: 60 degrees lowered command magnitude but lost too
  much gate progress. It should not mature.
- W&B evidence: `race/finished_rate`, `race/passed_gate_rate`, and hard-eval
  success did not improve.
- PPO/training evidence: no optimizer-collapse signal; do not change PPO
  hyperparameters.
- Structural evidence: the action-envelope implementation is train/eval matched
  through checkpoint metadata. A 75-degree ablation tests whether 60 degrees
  was simply too restrictive.
- External research evidence: the stateirving packet still supports v5
  local-obstacle observations, but local hard eval remains the acceptance gate.

## Approved Next Experiment

Name: `v5_action_envelope_75deg_from_loop020_25m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Structural parameter:

```text
action_rp_limit_deg=75.0
```

Train/eval chunk:

```text
30M steps, 5M checkpoint interval, milestone hard eval on config/level3_dr.toml
```

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_localobs_action_envelope_75deg \
  --proposal-name v5_action_envelope_75deg_from_loop020_25m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_action_envelope_75deg_after_loop023.md
```

## Promotion And Rollback

- Promote if hard eval beats loop020's `15%` success, `1.45` mean gates, or
  `85%` crash.
- Mature if it ties `15%` success while lowering command tilt or crash pressure.
- Reject if success stays at or below `5%` or mean gates stays below `1.15`.
- If 75 degrees also fails, stop action-envelope ablations and compare one final
  gate-acquisition reward rebalance against a stronger action-parameterization
  lane.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch another chunk without a new post-run analysis and 3-review
  decision after this experiment completes.
