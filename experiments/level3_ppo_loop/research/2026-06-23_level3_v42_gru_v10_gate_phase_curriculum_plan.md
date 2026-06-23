# Level3 V42 GRU/V10 Gate-Phase Curriculum Plan

Status: structural research packet for the next Level3 PPO loop lane.

## Scope

Final acceptance remains hard evaluation on unchanged `config/level3.toml`:

- success rate `>= 0.60`;
- mean successful time `<= 7.0s`;
- no Level3 track geometry, gate layout, obstacle layout, or randomization
  changes.

Deployment remains a single end-to-end PPO Actor:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is part of this packet.

## Local Evidence

loop112 / v40 tested true GRU-256 sequence memory with v10 phase/corridor/
aperture observation from scratch. It failed every milestone:

| Checkpoint | Success | Mean Gates | Crash | Timeout |
| --- | ---: | ---: | ---: | ---: |
| 1M | 0% | 0.0 | 64% | 36% |
| 2M | 0% | 0.0 | 57% | 43% |
| 3M | 0% | 0.0 | 52% | 48% |
| 4M | 0% | 0.0 | 54% | 46% |
| final | 0% | 0.0 | 53% | 47% |

The v41 audit then checked the suspected implementation layer and passed:

- v10 training/inference observation parity;
- action scale parity;
- recurrent train/inference Actor parity;
- hidden-state reset/carry parity;
- zero-update save/reload parity;
- recurrent PPO gradient/update sanity.

This means v40's zero-gate result is unlikely to be caused by an obvious
recurrent wiring bug. The more likely failure is that the from-scratch policy
never received enough learnable successful or near-successful gate approach
experience from the default initial-state distribution.

## Hypothesis

```text
v42_gru_v10_gate_phase_reset_curriculum_from_scratch
```

If the GRU/v10 wiring is clean but default from-scratch training never acquires
gate 0, then a training-only gate-phase reset curriculum should bootstrap local
gate acquisition. The hard evaluator remains unchanged, so any improvement must
transfer back to normal Level3 starts.

This lane changes one main factor from v40:

- add training-only `gate_phase_reset_prob=0.45` using the existing v33-style
  near-gate approach reset distribution.

It keeps fixed:

- train config: `config/level3.toml`;
- hard eval config: `config/level3.toml`;
- policy: `recurrent_actor_gru256`;
- observation: `level3_gate_corridor_aperture_margin_2obs_local_history_v10`;
- start: from scratch;
- reward scale: v39 gate-acquisition numbers;
- no planner, shield, MPC, or upper-level controller.

## First Screen

Training settings:

- horizon: `10M` environment steps;
- checkpoint interval: `1M`;
- hard-eval milestones: `1M, 2M, 3M, 4M, 5M, 8M, 10M`;
- rollout: `num_envs=256`, `num_steps=128`,
  `recurrent_sequence_len=128`.

Curriculum:

- `gate_phase_reset_prob=0.45`;
- `gate_phase_reset_x_min=-1.05`;
- `gate_phase_reset_x_max=-0.18`;
- `gate_phase_reset_yz_max=0.16`;
- `gate_phase_reset_speed_min=0.15`;
- `gate_phase_reset_speed_max=1.20`.

Fixed reward scale:

- `gate_stage_coef=13`;
- `gate_axis_coef=24`;
- `gate_front_bonus=5`;
- `gate_bonus=200`;
- `gate_back_bonus=35`;
- `finish_bonus=175`;
- `time_penalty=0.02`.

## Promotion And Rejection

Promote or mature if hard eval on `validation_unseen` shows one of:

- nonzero success;
- mean gates above `0.5`;
- clear passed-gate conversion compared with v40's all-zero gate result;
- crash reduction without merely replacing crashes with zero-gate timeouts.

Reject v42 as-is if:

- all milestones remain `0` mean gates;
- hard-eval behavior repeats v40's low-action timeout pattern;
- W&B shows local curriculum reward progress that does not convert into normal
  hard-eval gate progress.

If v42 produces gate progress but not stable success, the next packet may
mature the same hypothesis or add anti-drift/checkpoint retention. If v42 still
shows no gate acquisition, move away from from-scratch GRU/v10 and consider
success-trajectory imitation or a feed-forward/v5-controlled warm start.

