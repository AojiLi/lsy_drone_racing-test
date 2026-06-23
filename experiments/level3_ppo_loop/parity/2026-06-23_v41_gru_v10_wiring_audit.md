# V41 GRU/V10 Wiring Audit

Status: passed.

Audit lane:

```text
v41_gru_v10_recurrent_wiring_audit_and_zero_update_parity
```

Source trial:
`level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m`

Checkpoint audited:
`lsy_drone_racing/control/checkpoints/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_step_003000000.ckpt`

Command:

```bash
pixi run -e gpu python scripts/audit_level3_v41_gru_v10_wiring.py \
  --config level3.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_step_003000000.ckpt \
  --out experiments/level3_ppo_loop/parity/2026-06-23_v41_gru_v10_wiring_audit.json
```

The JSON output is generated locally and ignored by git; this markdown file is
the committed summary.

## Result

All required checks passed.

| Check | Result | Key Evidence |
| --- | --- | --- |
| checkpoint metadata | pass | policy `recurrent_actor_gru256`, observation `level3_gate_corridor_aperture_margin_2obs_local_history_v10`, obs dim `91`, GRU hidden `256` |
| observation parity and sanity | pass | train/inference v10 max abs diff `1.19e-7`; phase, corridor, and aperture sections nonzero |
| train/eval action-scale parity | pass | action low/high/scale/mean and sampled scaled actions all diff `0.0` |
| train/inference recurrent Actor parity | pass | action, logprob, entropy, value, and next hidden diffs all `0.0` |
| zero-update save/reload parity | pass | action, logprob, entropy, value, and next hidden diffs all `0.0` |
| hidden-state reset/carry parity | pass | sequence-vs-step action diff `5.96e-8`; done reset exactly matches zero hidden |
| recurrent PPO gradient/update sanity | pass | nonzero gradients for actor_pre, actor_gru, actor_post, actor_logstd, critic; one update moved deterministic action by `0.1399` |

## Interpretation

The v40 failure is not explained by an obvious GRU/v10 wiring bug.

The audit rules out the main suspected implementation problems:

- training and inference v10 observation flattening match;
- action scaling matches the training wrapper;
- recurrent train-side and inference-side networks produce identical outputs;
- hidden state is carried and reset correctly;
- checkpoint load/save without updates preserves deterministic outputs;
- recurrent Actor parameters and `actor_logstd` receive gradients and can move.

Therefore loop112's hard-eval collapse to `0%` success and `0.0` mean gates is
more likely a learning-distribution problem: from-scratch GRU/v10 did not
bootstrap first-gate acquisition under the default start-state distribution.

## Consequence

Do not continue v40 as-is and do not start from loop112 checkpoints. The next
structural lane should keep hard eval on unchanged `config/level3.toml`, but
change the training distribution so the recurrent policy sees learnable
near-gate approach states.

The approved follow-up lane is:

```text
v42_gru_v10_gate_phase_reset_curriculum_from_scratch
```

