# V46 Residual Frontier Teacher Action Preflight

Status: passed.

## Scope

- Final evaluation target remains unchanged `config/level3.toml`.
- No Level3 track geometry, gate layout, obstacle layout, or randomization changes.
- Teacher data is training-only; deployment remains PPO Actor only.

## Checks

- teacher checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt`
- student checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt`
- teacher policy arch: `mlp_residual_recurrent_actor_gru256`
- student policy arch: `mlp_2x_tanh`
- checked steps: `308`
- max extracted-vs-direct scaled action diff: `0`
- max extracted-vs-direct hidden-state diff: `0`
- max residual branch contribution: `0.0432441831`
- mean residual branch contribution: `0.0249703883`
- p95 residual branch contribution: `0.0388249569`
- success seeds: `[4501]`
- samples written: `308`
- student-vs-teacher KL on generated dataset: `0.152495578`
- student-vs-teacher action MSE: `0.0408469252`
- student action agreement within 0.15: `0.708603919`
- dataset path: `experiments/level3_ppo_loop/retention_datasets/v46_loop107_residual_frontier_diagnostic_v5.npz`

## Decision

Residual-GRU teacher action extraction is parity-proven for loop107/v37 1M:
the dataset path includes the residual branch and matches direct
`ppo_level3_inference` action and hidden-state evolution on ordered
trajectories.

The generated `.npz` remains a local training artifact and must stay out of git.
