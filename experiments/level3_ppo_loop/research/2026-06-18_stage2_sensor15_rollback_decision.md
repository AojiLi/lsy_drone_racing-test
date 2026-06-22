# Level3 PPO Stage 2 Decision: Roll Back Sensor-Range Staging Probe

## Scope

This is a post-run Stage 2 decision report for:

```text
level3_loop_008_stage2_gate0_sensor15_probe
```

It does not approve another training run. It does not approve reward, PPO,
observation, network, environment, curriculum, or training-structure changes.

## Verdict

Roll back / hold the `sensor_range=1.5` staging direction.

Do not continue from the 008 checkpoint. Keep the global incumbent:

```text
lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

Next recommended artifact:

```text
Stage 2 observation/event parity packet
```

## Hard-Eval Result

Hard evaluation stayed on the original target config:

```text
config/level3_dr.toml
```

Best 008 checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_008_stage2_gate0_sensor15_probe/level3_loop_008_stage2_gate0_sensor15_probe_step_015000000.ckpt
```

Metrics:

| Checkpoint | Success | Crash | Mean gates | Target met |
| --- | ---: | ---: | ---: | --- |
| Global incumbent `001:final` | `0.0` | `1.0` | `0.85` | no |
| Stage2 sensor15 best `008:15M` | `0.0` | `1.0` | `0.75` | no |

The probe did not meet any acceptance criterion:

- `success_rate > 0.0`: no
- `mean_gates > 0.85`: no
- `crash_rate < 1.0`: no
- linked target-gate `0`/`1` crash-taxonomy improvement with evaluator
  progress: no

## W&B Result

W&B run:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_008_stage2_gate0_sensor15_probe
```

Analyzer report:

```text
experiments/level3_ppo_loop/analysis/level3_loop_008_stage2_gate0_sensor15_probe_analysis.md
```

Relevant W&B evidence:

- `race/finished_rate`: `0.0`, flat.
- `race/passed_gate_rate`: tail mean `0.009338`, flat.
- `race/gate_stage`: tail mean `0.161118`, down.
- `race/gate_axis_x`: tail mean `-0.942158`, flat.
- `losses/approx_kl`: tail mean `0.00222`, below `target_kl=0.03`.
- `losses/clipfrac`: tail mean `0.002805`, low.
- `losses/entropy`: not collapsed.

Interpretation:

- No gate/finish conversion.
- No PPO-instability signature.
- The `sensor_range=1.5` staging hypothesis is not supported by this run.

## Crash Taxonomy

Crash taxonomy command:

```text
pixi run -e gpu python scripts/analyze_level2_ppo_crashes.py \
  --mode single \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_008_stage2_gate0_sensor15_probe/level3_loop_008_stage2_gate0_sensor15_probe_step_015000000.ckpt \
  --seed-start 1 \
  --num-seeds 40 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_loop_008_15M_crash_taxonomy
```

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_008_15M_crash_taxonomy_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_008_15M_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_008_15M_crash_taxonomy_hotspots.png`

Result:

- Episodes: `40`
- Successes: `0`
- Crashes: `40`
- Timeouts: `0`
- Crashes by target gate:
  - gate `1`: `19`
  - gate `0`: `17`
  - gate `2`: `4`

Comparison:

- Incumbent 001 crash taxonomy had target gate `0/1` crashes: `34/40`.
- 008 best checkpoint has target gate `0/1` crashes: `36/40`.

This does not show a linked crash-taxonomy improvement.

## Subagent Consensus

Evaluator reviewer:

- 008 did not improve hard evaluator metrics.
- Best 008 checkpoint is `15M`, but it has `success_rate=0.0`,
  `crash_rate=1.0`, `mean_gates=0.75`.
- Acceptance criteria were not met.

W&B/PPO reviewer:

- No gate/finish conversion.
- PPO metrics look stable, not blown up.
- Sensor-range staging is not supported.

Tuning/decision reviewer:

- Roll back / hold the `sensor_range=1.5` staging direction.
- Do not continue from 008.
- Do not keep raising `sensor_range`.
- Next Stage 2 packet should focus on observation/event parity.

## Decision

Hold here.

The next useful work is a narrow diagnostic/proposal packet for observation and
event parity, for example:

- compare training `RaceObservation` with inference `_obs_rl` on identical
  reset and rollout states;
- verify observed nominal versus actual gate positions around gate-passing
  events;
- instrument gate-plane crossing, wrong-side, front/back, and target-gate
  update counters on deterministic traces;
- verify that reward event geometry is aligned with hard-eval success
  semantics.

Do not start another train/eval chunk until that packet is written and dry-run.
