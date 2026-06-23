# Level3 Sequence-Memory GRU Phase-Corridor Plan

Status: structural research packet for the next Level3 PPO loop lane.

## Scope

Final acceptance remains hard evaluation on unchanged `config/level3.toml`:

- success rate `>= 0.60`;
- mean successful time `<= 7.0s`;
- no Level3 track geometry, gate layout, obstacle layout, or randomization changes.

Deployment remains a single end-to-end PPO Actor:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is part of this packet.

## Local Evidence

Recent hard-eval evidence has plateaued around 19%-21% success:

| Lane | Best hard eval |
| --- | --- |
| loop101 / v33 gate-phase reset | 20% success, 1.69 mean gates, 80% crash |
| loop107 / v37 residual-GRU transfer | 21% success, 1.66 mean gates, 79% crash at 1M |
| loop108 / v37b residual-GRU continuation | 18% success, 1.58 mean gates, 82% crash |
| loop109 / v38 residual-GRU teacher retention | 18% success, 1.64 mean gates, 82% crash |
| loop110 / v39 feed-forward gate acquisition | 21% success, 1.64 mean gates, 79% crash at 3M |

The successful validation seed sets churn rather than accumulate. Across
loop101, loop107, and loop110, the union contains 34 success seeds, but only 9
seeds are solved by all three. This looks like local policy reshuffling, not a
stable multi-gate capability gain.

Failures remain dominated by contact/bounds-or-ground crashes, not timeouts.
That points to unstable continuous gate approach, obstacle interaction, and
phase-to-phase control rather than speed.

## Diagnosis

The bottleneck is not simply reward scale. The current MLP and residual-GRU
routes can learn some local reactions, but they do not reliably carry useful
state across the multi-gate episode. v38 teacher retention preserved the
feed-forward teacher too strongly: retention metrics were active, but hard eval
did not improve.

The next test should isolate sequence memory with richer local geometry:

- use a true `recurrent_actor_gru256`, not residual-only memory;
- expose phase, corridor, and aperture-margin features so the GRU does not need
  to infer every subtask boundary from short v5 history;
- keep reward numbers fixed to the v39 gate-acquisition scale during the first
  screen, so the main variable is memory/observation structure;
- use dense milestone evaluation and select the best milestone checkpoint, not
  final by default.

## Approved First Screen

```text
v40_sequence_memory_gru_phase_corridor_from_scratch
```

Training settings:

- train config: `config/level3.toml`;
- hard eval config: `config/level3.toml`;
- policy: `recurrent_actor_gru256`;
- observation:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`;
- start: from scratch;
- horizon: 5M environment steps;
- checkpoint interval: 1M;
- hard-eval milestones: 1M, 2M, 3M, 4M, 5M;
- rollout: `num_envs=256`, `num_steps=128`,
  `recurrent_sequence_len=128`.

Fixed reward scale for this first screen:

- `gate_stage_coef=13`;
- `gate_axis_coef=24`;
- `gate_front_bonus=5`;
- `gate_bonus=200`;
- `gate_back_bonus=35`;
- `finish_bonus=175`;
- `time_penalty=0.02`.

These numbers are inherited from v39 as the current strongest gate-acquisition
motivation. They are not the search variable in this packet.

## Promotion And Rejection

Promote or mature only if hard eval on `validation_unseen` shows one of:

- success clearly above the 21% frontier;
- success in roughly the 25%-30% range;
- mean gates above 1.75 with lower crash, even if success has not yet jumped.

Reject v40 as-is if:

- success remains `<= 21%`;
- mean gates stay near the 1.6 plateau;
- crash remains near 79%-83%;
- later checkpoints repeat the loop107/loop110 drift pattern.

If v40 shows a memory signal but drifts, the next structural packet should add
sequence-level success-trajectory pretraining or imitation. Do not reuse v38
online teacher retention as-is, because that preserved teacher behavior without
creating new memory capability.

