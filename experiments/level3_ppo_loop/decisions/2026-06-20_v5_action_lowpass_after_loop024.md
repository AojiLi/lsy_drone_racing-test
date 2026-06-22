# Level3 Decision: V5 Action Lowpass After Loop 024

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_024_v5_action_envelope_75deg_from_loop020_25m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m_step_025000000.ckpt`
- Hard-eval success rate: `0.05`
- Mean successful time: `5.82s`
- Crash rate: `0.95`
- Mean gates: `0.95`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Loop024 does not improve the hard-eval frontier. It
  regressed from loop020's `15%` success, `1.45` mean gates, and `85%` crash to
  `5%`, `0.95`, and `95%`. Do not continue the 75-degree envelope.
- `wandb_ppo_diagnostics`: Stop 60/75-degree action-envelope ablations. PPO is
  stable enough; W&B race conversion remains flat. A final gate-acquisition
  reward rebalance is possible, but action envelopes did not solve behavior.
- `structure_research_synthesis`: Reject the blunt envelope family. Keep full
  `90deg` authority but shape command dynamics with train/eval-matched
  low-pass filtering.

## Main-Agent Decision

Selected decision: `launch_named_structural_lane`

Reject `v5_localobs_action_envelope_60deg` and
`v5_localobs_action_envelope_75deg`. Launch
`v5_localobs_action_lowpass_90deg`. Keep `config/level3_dr.toml` immutable and
as the hard-eval target, keep v5 observation, keep PPO hyperparameters
unchanged, keep loop020 completion-backloaded reward numbers, and start again
from the loop020 25M global-best checkpoint.

The structural change is `action_lowpass_alpha=0.35` with
`action_rp_limit_deg=90.0`: the policy keeps the full attitude-command envelope
but the normalized action is low-pass filtered before reward, simulator step,
observation `last_action`, checkpoint save, and hard-eval inference.

## Rationale

- Local evaluator evidence: both 60 and 75-degree envelopes reduced or shaped
  commands but lost hard-eval gate progress. Limiting authority is not the right
  next lever.
- W&B evidence: training reward signals still do not convert into passed gates,
  finishes, or lower hard-eval crash rate.
- PPO/training evidence: no PPO instability justifies optimizer or network
  changes.
- Structural/code evidence: low-pass filtering is now train/eval matched via
  checkpoint metadata. Old checkpoints default to `action_lowpass_alpha=1.0`.
- External research evidence: the stateirving v5 evidence remains useful, but
  local hard eval shows command dynamics are the next structural bottleneck.

## Implemented Structural Support

- `lsy_drone_racing/control/ppo_level3_observation.py`:
  checkpoint metadata now stores and validates `action_lowpass_alpha`; old
  checkpoints default to `1.0`.
- `lsy_drone_racing/control/train_CleanRL_ppo_level3.py`:
  training accepts `action_lowpass_alpha`; `RaceObservation` filters normalized
  actions before passing them to reward/env and records the filtered action as
  `last_action`.
- `lsy_drone_racing/control/ppo_level3_inference.py`:
  hard-eval inference reads `action_lowpass_alpha` from the checkpoint and
  applies the same normalized-action filter before scaling physical actions.
- `scripts/level3_ppo_loop.py`:
  adds the named structural hypothesis `v5_localobs_action_lowpass_90deg`.

## Approved Next Experiment

Name: `v5_action_lowpass_90deg_from_loop020_25m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Structural parameters:

```text
action_rp_limit_deg=90.0
action_lowpass_alpha=0.35
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
  --structural-hypothesis v5_localobs_action_lowpass_90deg \
  --proposal-name v5_action_lowpass_90deg_from_loop020_25m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_action_lowpass_after_loop024.md
```

## Promotion And Rollback

- Promote if hard eval beats loop020's `15%` success, `1.45` mean gates, or
  `85%` crash.
- Mature if it ties `15%` success while reducing command/action volatility.
- Reject if success stays at or below `5%` or mean gates below `1.15`.
- If this lane fails, stop action-dynamics ablations and run the explicit
  gate-acquisition reward rebalance or hold for a broader controller design.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch another chunk without a new post-run analysis and 3-review
  decision after this experiment completes.
