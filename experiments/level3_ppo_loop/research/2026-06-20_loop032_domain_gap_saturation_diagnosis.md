# loop032 Domain-Gap And Command-Saturation Diagnosis

Date: 2026-06-20

## Purpose

Diagnose the failure after:

`level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`

This packet is diagnostic evidence for the next main-agent decision. It does
not approve a training run by itself.

## Summary

loop032 should not be continued.

The failure is not explained by a simple train/eval config domain gap. The best
loop032 checkpoint fails both:

- hard-eval config: `level3_dr.toml`
- its own training config: `level3_dr_stage2_no_train_wrappers.toml`

The strongest remaining diagnosis is:

- v5 observation and action wiring are clean;
- no-wrapper curriculum training degraded the loop020 policy;
- PPO updates are weak/ineffective while command saturation rises;
- reward and W&B gate-stage proxies still do not convert into stable hard gate
  passage.

## Source Trial

loop032:

- train config:
  `level3_dr_stage2_no_train_wrappers.toml`
- hard eval config:
  `level3_dr.toml`
- observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`

Best loop032 hard-eval checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_step_010000000.ckpt`
- success rate: `0.0`
- crash rate: `1.0`
- mean gates: `0.8`
- command tilt over-limit fraction: `0.7672794535902253`

Global best remains loop020:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- success rate: `0.15`
- crash rate: `0.85`
- mean gates: `1.45`
- mean successful time: `6.366666666666667s`
- command tilt over-limit fraction: `0.5800860395510893`

## Parity Diagnostics

The v5 observation/event parity script was updated so the training-side probe
uses the checkpoint's observation layout and action low-pass metadata.

### v5 Observation/Event Parity

Command:

```bash
pixi run -e gpu python scripts/check_level3_observation_event_parity.py \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --seed-start 1 \
  --num-seeds 20 \
  --max-steps 300 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_v5_loop020_25M
```

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_v5_loop020_25M_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_v5_loop020_25M_observation_rows.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_v5_loop020_25M_event_rows.csv`

Result:

- clean: `true`
- train dim: `68`
- inference dim: `68`
- max observation diff: `4.76837158203125e-07`
- observation failure count: `0`
- passed-gate mismatch count: `0`
- finished mismatch count: `0`
- timeout mismatch count: `0`

### v5 Action Scaling Parity

Command:

```bash
pixi run -e gpu python scripts/check_level3_action_scaling_parity.py \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --seed 1 \
  --samples 1000 \
  --out experiments/level3_ppo_loop/diagnostics/level3_action_scaling_parity_v5_loop020_25M.json
```

Artifact:

- `experiments/level3_ppo_loop/diagnostics/level3_action_scaling_parity_v5_loop020_25M.json`

Result:

- clean: `true`
- action low/high diff: `0.0`
- action scale/mean diff: `0.0`
- sampled scaled-action diff: `0.0`

Interpretation:

- Do not spend the next training attempt on fixing v5 observation wiring.
- Do not spend the next training attempt on action scaling parity.

## Crash And Domain Diagnostics

### loop020 Best On Hard Config

Command:

```bash
pixi run -e gpu python scripts/analyze_level2_ppo_crashes.py \
  --mode single \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --seed-start 1 \
  --num-seeds 40 \
  --inference-module ppo_level3_inference \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_loop_020_25M_v5_hard_crash_taxonomy_40seed
```

Result:

- successes: `3/40`
- success rate: `0.075`
- crash rate: `0.925`
- mean successful time: `5.966666666666666s`
- crashes by target gate: `0:16`, `1:14`, `2:6`, `3:1`

Artifact:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_020_25M_v5_hard_crash_taxonomy_40seed_summary.json`

### loop032 Best On Hard Config

Command:

```bash
pixi run -e gpu python scripts/analyze_level2_ppo_crashes.py \
  --mode single \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_step_010000000.ckpt \
  --seed-start 1 \
  --num-seeds 40 \
  --inference-module ppo_level3_inference \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_loop_032_10M_v5_hard_crash_taxonomy_40seed
```

Result:

- successes: `0/40`
- success rate: `0.0`
- crash rate: `1.0`
- crashes by target gate: `0:16`, `1:15`, `2:9`

Artifact:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_032_10M_v5_hard_crash_taxonomy_40seed_summary.json`

### loop032 Best On No-Wrapper Training Config

Command:

```bash
pixi run -e gpu python scripts/analyze_level2_ppo_crashes.py \
  --mode single \
  --config level3_dr_stage2_no_train_wrappers.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_step_010000000.ckpt \
  --seed-start 1 \
  --num-seeds 40 \
  --inference-module ppo_level3_inference \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_loop_032_10M_v5_no_wrappers_crash_taxonomy_40seed
```

Result:

- successes: `0/40`
- success rate: `0.0`
- crash rate: `1.0`
- crashes by target gate: `0:16`, `1:15`, `2:9`

Artifact:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_032_10M_v5_no_wrappers_crash_taxonomy_40seed_summary.json`

Interpretation:

- loop032 is not failing only because hard eval includes train-only robustness
  wrappers that the no-wrapper training config omitted.
- The policy is also unusable under the easier no-wrapper config.
- The no-wrapper curriculum lane should be rejected for now.

## Command-Saturation Pattern

Selected v5 hard-eval records:

| Trial | Success | Mean Gates | Crash | Cmd Tilt Over-Limit | Mean Action Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| loop020 completion-backloaded | `0.15` | `1.45` | `0.85` | `0.5801` | `0.3672` |
| loop031 legacy centerline safety | `0.05` | `1.10` | `0.95` | `0.6089` | `0.5426` |
| loop032 no-wrapper curriculum | `0.0` | `0.80` | `1.0` | `0.7673` | `0.5346` |

Interpretation:

- The best local policy already uses substantial command tilt.
- Regressed branches often raise command saturation and action delta without
  improving gate conversion.
- loop025 reduced command saturation (`0.3341`) but did not improve success
  enough, suggesting that simply smoothing actions is not sufficient.

## Recommended Next Direction

Do not continue:

- `v5_curriculum_gate_obstacle_staged_training`
- more no-wrapper training from loop020
- another gate-potential maturation without a new mechanism
- another reward-number tweak whose only justification is W&B gate-stage proxy
  improvement

The next runnable hypothesis should be a named structural/training lane that
directly targets PPO update pressure and command saturation from the loop020
checkpoint while keeping:

- hard eval on `level3_dr.toml`;
- v5 local-obstacle observation;
- level3 track geometry/randomization unchanged;
- one bounded 20M-30M train/eval chunk;
- milestone hard evaluation and post-run analysis.

Reason:

- W&B repeatedly shows very low KL, near-zero clip fraction, tiny policy loss,
  high entropy, and proxy learning without pass conversion.
- Hard eval shows command saturation rising as branches regress.
- Parity checks do not point to wiring bugs.

A candidate next lane should be proposed in a separate main-agent decision
packet before training. This packet alone is diagnostic evidence, not training
approval.
