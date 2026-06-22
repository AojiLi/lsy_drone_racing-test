# Level3 PPO Stage 2 Code Rollback: Gate-Box Reward Geometry

## Decision

The Stage 2 gate-box reward geometry experiment was rejected after
`level3_loop_009_stage2_gate_box_reward_geometry` failed to improve hard eval
metrics. The training reward geometry has been returned to the pre-experiment
circular `gate_stage_radius` logic.

## Reverted Behavior

- `missed_gate` again uses circular gate-plane distance.
- `gate_front`, `gate_back`, and tracked back hits again use
  `gate_stage_radius`.
- `wrong_side` again uses circular centerline distance.

## Preserved Behavior

- The inference rotmat parity fix remains in place.
- W&B and loop infrastructure changes remain in place.
- The next Stage 2 branch should not continue from the rejected gate-box reward
  geometry semantics.

## Verification

- `pixi run -e gpu python -m py_compile lsy_drone_racing/control/train_CleanRL_ppo.py lsy_drone_racing/control/train_CleanRL_ppo_level3.py`
- `git diff --check -- lsy_drone_racing/control/train_CleanRL_ppo.py lsy_drone_racing/control/train_CleanRL_ppo_level3.py`
