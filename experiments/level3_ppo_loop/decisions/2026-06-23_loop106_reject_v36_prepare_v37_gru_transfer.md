# Decision: Reject v36 and Prepare v37 GRU Transfer

Decision: `launch_named_structural_lane`

Pending gate resolved by this packet:

- trial:
  `level3_loop_106_structural_v36_online_level_replay_loop101_10m`
- analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_106_structural_v36_online_level_replay_loop101_10m_analysis.md`
- analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_106_structural_v36_online_level_replay_loop101_10m_analysis.json`

Approved next lane:
`v37_gru_transfer_memory_structure_from_loop101`

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization to make the metric easier.
- Do not start from loop102, loop103, or loop106 checkpoints.
- Start from loop101 final, the current global frontier checkpoint.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

loop106/v36 tested online competence-gated level replay from loop101 for 10M
steps.

Global best remains loop101 final:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt`
- success: `20/100`
- mean gates: `1.69`
- crash rate: `80%`
- mean successful time: `6.873s`

Best loop106 checkpoint was only the 1M checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_106_structural_v36_online_level_replay_loop101_10m/level3_loop_106_structural_v36_online_level_replay_loop101_10m_step_001000000.ckpt`
- success: `20/100`
- mean gates: `1.63`
- crash rate: `80%`
- mean successful time: `7.744s`

Later loop106 checkpoints regressed:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| 1M | 20% | 1.63 | 80% | 7.744s |
| 2M | 17% | 1.62 | 83% | 7.394s |
| 3M | 10% | 1.37 | 90% | 7.292s |
| 5M | 15% | 1.58 | 85% | 7.453s |
| 8M | 14% | 1.45 | 86% | 7.569s |
| 9M | 14% | 1.49 | 86% | 7.310s |
| final | 14% | 1.41 | 86% | 7.341s |

v36 did not pass its promotion gate:

- no checkpoint exceeded `20%` success;
- no checkpoint exceeded `1.69` mean gates with crash `<=80%`;
- hard eval showed late-checkpoint collapse after the 1M checkpoint.

## Reviewer Synthesis

- Evaluator reviewer: reject v36. It only ties loop101 on success/crash at 1M,
  while mean gates and time are worse; final collapses to `14%` success and
  `86%` crash.
- W&B/PPO reviewer: PPO did not explode. Approximate KL and clip fraction stayed
  low, entropy and explained variance were stable, and value loss did not
  blow up. The failure is conversion: competence gates remained closed and
  training signals did not become validation-unseen progress.
- Structure/research reviewer: reject v36 and stop replay-probability tuning.
  The next lane should test memory through a GRU transfer / memory-structure
  packet from loop101, not a from-scratch GRU repeat.

## Approved v37 Scope

`v37_gru_transfer_memory_structure_from_loop101`

The next stage is an implementation and verification lane before training:

- Initial checkpoint source:
  loop101 final checkpoint listed above.
- Train config:
  unchanged `config/level3.toml`.
- Hard eval config:
  unchanged `config/level3.toml`.
- Actor observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Controller:
  end-to-end PPO Actor only.
- Actor architecture:
  GRU-256 memory lane, using the existing recurrent Actor support as the base.
- Transfer:
  create explicit MLP-to-GRU initialization support from loop101 instead of
  starting GRU from scratch.
- Required checks before any long training:
  hidden-state reset on episode boundaries, sequence rollout/BPTT behavior,
  checkpoint metadata, inference hidden-state reset, and a bounded zero-update
  or deterministic parity packet where meaningful for the transfer design.

## Not Approved

- Do not continue v36.
- Do not tune v36 replay probability.
- Do not launch a from-scratch GRU repeat of the old loop062 lane.
- Do not change reward numbers as the next action.
- Do not change `config/level3.toml`.

## Next Action

Implement and test v37 GRU transfer / memory-structure support. The next
training command may only be launched after the support tests and transfer
preflight packet pass. If the implementation cannot preserve useful behavior
from loop101, hold and write a more conservative GRU distillation or memory
pretraining packet instead of launching training.
