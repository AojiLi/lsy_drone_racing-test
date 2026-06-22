# v32 Privileged Critic Zero-Update Parity

Status: `passed`

## Scope

- Source checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_step_012000000.ckpt`.
- v32 checkpoint: `lsy_drone_racing/control/checkpoints/level3_v32_parity/level3_loop_097_12m_v32_privileged_critic_zero_update.ckpt`.
- Actor observation is unchanged; only the Critic input layer is widened.
- Final evaluator config remains `config/level3.toml`.

## Metadata

```json
{
  "action_dim": 4,
  "actor_observation_dim": 68,
  "critic_observation_dim": 135,
  "hidden_dim": 256,
  "observation_layout": "level3_target_gate_nearest_gate_2obs_local_history_v5",
  "source_checkpoint": "/home/aojili/lsy_drone_racing/lsy_drone_racing/control/checkpoints/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_step_012000000.ckpt",
  "target_checkpoint": "lsy_drone_racing/control/checkpoints/level3_v32_parity/level3_loop_097_12m_v32_privileged_critic_zero_update.ckpt"
}
```

## Validation Summary

| Metric | source | v32 zero-update |
| --- | ---: | ---: |
| `success_count` | `20` | `20` |
| `success_rate` | `0.2` | `0.2` |
| `crash_rate` | `0.8` | `0.8` |
| `timeout_rate` | `0.0` | `0.0` |
| `mean_gates` | `1.66` | `1.66` |
| `mean_time_s_success` | `7.055` | `7.055` |
| `success_seeds` | `[112, 120, 121, 123, 134, 136, 138, 142, 148, 153, 155, 160, 161, 167, 169, 170, 184, 185, 192, 194]` | `[112, 120, 121, 123, 134, 136, 138, 142, 148, 153, 155, 160, 161, 167, 169, 170, 184, 185, 192, 194]` |
| `termination_reasons` | `{"contact": 80, "finish": 20}` | `{"contact": 80, "finish": 20}` |
