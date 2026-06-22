# Level3 Decision: V5 Action Envelope After Loop 022

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_022_v5_completion_micro_safety_from_loop020_25m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_022_v5_completion_micro_safety_from_loop020_25m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_022_v5_completion_micro_safety_from_loop020_25m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_022_v5_completion_micro_safety_from_loop020_25m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_022_v5_completion_micro_safety_from_loop020_25m/level3_loop_022_v5_completion_micro_safety_from_loop020_25m_step_020000000.ckpt`
- Hard-eval success rate: `0.05`
- Mean successful time: `6.68s`
- Crash rate: `0.95`
- Mean gates: `1.10`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Reject loop022. It regressed from loop020 (`15%`
  success, `1.45` mean gates, `85%` crash) to `5%` success, `1.10` mean gates,
  and `95%` crash. Two post-loop020 reward-number safety attempts failed to
  beat the global best, so evaluator evidence supports a structural lane.
- `wandb_ppo_diagnostics`: PPO is not collapsing. KL, clipfrac, entropy, and
  explained variance are acceptable, but W&B gate rewards still do not convert
  into hard-eval success. A final gate-acquisition reward rebalance would be
  possible, but another safety micro-tweak is not justified.
- `structure_research_synthesis`: Recommend a named structural lane. The v5
  observation wiring is consistent, but command tilt and action delta remain
  high. Test a train/eval-matched roll/pitch action envelope so the policy
  cannot rely on near-90-degree commands.

## Main-Agent Decision

Selected decision: `launch_named_structural_lane`

Launch `v5_localobs_action_envelope_60deg`. Keep the Level3 track immutable,
keep hard eval on `config/level3_dr.toml`, keep v5 local-obstacle observation,
and keep PPO hyperparameters unchanged. The structural change is only the
policy action envelope: roll/pitch normalized actions now scale to `+/-60deg`
instead of `+/-90deg`, with that envelope saved in checkpoints and reused by
the hard-eval inference controller.

## Rationale

- Local evaluator evidence: loop020 remains the global best at `15%` success and
  `1.45` mean gates. Loop021 and loop022 both started from loop020 25M and
  regressed under reward-number safety changes.
- W&B evidence: reward components can rise while passed-gate, finished, and
  crash rates remain flat. The current reward family is not converting reliably.
- PPO/training evidence: PPO diagnostics do not justify changing optimizer,
  entropy, target KL, minibatches, epochs, hidden dim, or `n_obs`.
- Structural/code evidence: training and inference both scale normalized
  actions to attitude commands. The new lane makes this scaling explicit and
  matched by storing `action_rp_limit_deg` in checkpoints.
- External research evidence: the stateirving packet still supports the v5
  local-obstacle observation family, but remote results also plateau far below
  target. The local failure mode now points to action-envelope/control behavior,
  not another observation-layout swap.

## Implemented Structural Support

- `lsy_drone_racing/control/ppo_level3_observation.py`:
  checkpoint metadata now stores and validates `action_rp_limit_deg`; old
  checkpoints default to `90.0`.
- `lsy_drone_racing/control/train_CleanRL_ppo_level3.py`:
  training accepts `action_rp_limit_deg`, applies it in normalized action
  scaling, uses the same envelope for command-tilt reward calculations, and
  writes it to checkpoints.
- `lsy_drone_racing/control/ppo_level3_inference.py`:
  hard-eval inference reads `action_rp_limit_deg` from the checkpoint and uses
  the same roll/pitch envelope in `_scale_action`.
- `scripts/level3_ppo_loop.py`:
  adds the named structural hypothesis `v5_localobs_action_envelope_60deg`.

## Approved Next Experiment

Name: `v5_action_envelope_60deg_from_loop020_25m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Observation layout:

```text
level3_target_gate_nearest_gate_2obs_local_history_v5
```

Structural parameter:

```text
action_rp_limit_deg=60.0
```

Reward/PPO parameters:

Use the loop020 completion-backloaded reward family and unchanged PPO structure
from the built-in `v5_localobs_action_envelope_60deg` hypothesis.

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
  --structural-hypothesis v5_localobs_action_envelope_60deg \
  --proposal-name v5_action_envelope_60deg_from_loop020_25m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_022_v5_completion_micro_safety_from_loop020_25m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_action_envelope_after_loop022.md
```

## Promotion And Rollback

- Promote if hard eval beats loop020's `15%` success, `1.45` mean gates, or
  `85%` crash.
- Mature to 60M if it ties `15%` success while materially lowering command tilt
  or crash pressure.
- Reject if success stays at or below `5%` or mean gates stays below `1.15`.
- If this lane fails, do not keep changing safety reward numbers. The next
  decision should compare one final gate-acquisition reward rebalance against a
  more explicit controller/training-structure lane.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch another chunk without a new post-run analysis and 3-review
  decision after this experiment completes.
