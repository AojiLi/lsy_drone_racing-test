# Level3 PPO Stage 2 Proposal: Gate-Box Reward Geometry Alignment

## Scope

This is a narrow Stage 2 proposal. It does not start training.

Allowed change family:

- align existing shaped gate-event geometry with the hard gate box used by
  `lsy_drone_racing.envs.utils.gate_passed`.

Not allowed in this packet:

- observation layout changes;
- PPO hyperparameter changes;
- network changes;
- algorithm changes;
- environment or track changes;
- curriculum/staging changes;
- new reward channels;
- changing W&B/project plumbing;
- continuing from the failed `008` sensor-range checkpoint.

## Current Evidence

The corrected current best is:

```text
lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt
```

Fixed-inference hard eval:

- `success_rate=0.0`
- `crash_rate=1.0`
- `mean_gates=0.9`
- `mean_time_s_success=null`
- `score=-71.4`

Observation/event parity is now clean:

- after-fix observation max abs diff: `4.76837158203125e-7`
- after-fix observation failures: `0`
- hard/reward passed-gate mismatches: `0`
- finish mismatches: `0`
- timeout mismatches: `0`

Crash taxonomy for the refreshed best:

- episodes: `40`
- successes: `0`
- crashes: `40`
- crashes by target gate:
  - gate `0`: `17`
  - gate `1`: `15`
  - gate `2`: `8`
- top likely objects:
  - `gate_0_top`: `9`
  - `obstacle_0`: `6`
  - `gate_0_left`: `3`
  - `obstacle_1`: `3`
- nearest gate part counts:
  - `top`: `14`
  - `stand`: `9`
  - `left`: `7`
  - `right`: `6`
  - `bottom`: `4`

Synthetic gate-plane threshold grid:

- hard gate pass uses box half width `0.225m`;
- shaped `front/back` uses radius `0.24m`;
- shaped `missed` uses radius `0.25m`;
- hard-pass points outside stage radius: `1141 / 19881`;
- stage-radius points outside hard box: `250 / 19881`;
- hard-fail points not missed by reward radius: `578 / 19881`.

## Hypothesis

The policy is learning partial gate acquisition but still crashes at gate edges
and nearby obstacles. The hard pass event itself is aligned, but the shaped
intermediate events are circular while the hard gate pass is a square box.

This can make the dense shaping ambiguous near edges/corners:

- some hard-valid gate-box regions are outside the shaped front/back circle;
- some shaped-valid circle regions are outside the hard gate box;
- some hard-fail plane crossings are not counted as `missed_gate` because they
  are outside the hard box but inside the `0.25m` radius.

The next experiment should test whether aligning shaped event geometry to the
hard gate box improves gate acquisition without changing algorithm or
observation semantics.

## Proposed Code Change

In `Level2RaceReward` in both training files:

- `lsy_drone_racing/control/train_CleanRL_ppo.py`
- `lsy_drone_racing/control/train_CleanRL_ppo_level3.py`

add a helper equivalent to the hard gate-box check in Y/Z:

```python
def _inside_gate_box_yz(self, yz):
    half_y = 0.225
    half_z = 0.225
    return (abs(yz[:, 0]) < half_y) & (abs(yz[:, 1]) < half_z)
```

Then use that predicate for existing shaped events:

- `front_hit`: replace `centerline_dist < gate_stage_radius` with hard-box
  Y/Z check at the front stage plane;
- `back_hit_on_pass`: replace `back_plane_dist < gate_stage_radius` with
  hard-box Y/Z check;
- `back_hit_tracked`: replace `tracked_back_plane_dist < gate_stage_radius`
  with hard-box Y/Z check;
- `missed_gate`: replace `gate_plane_dist > 0.25` with
  `~inside_gate_box_yz(plane_yz)`;
- `wrong_side_gate`: replace the circular centerline predicate with an
  outside-hard-box predicate after crossing behind the gate.

Keep all existing reward channels and coefficients. Do not add new terms.

## Training Proposal

If this packet is accepted, run one bounded train/eval chunk only:

```text
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --research-packet experiments/level3_ppo_loop/research/2026-06-18_stage2_gate_box_reward_geometry_proposal.md
```

Required starting checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt
```

Required hard eval config:

```text
config/level3_dr.toml
```

Required W&B project:

```text
ADR-PPO-Racing-Level3
```

## Acceptance

Accept only if hard evaluation on `config/level3_dr.toml` shows at least one of:

- `success_rate > 0.0`;
- `mean_gates > 0.9`;
- `crash_rate < 1.0`;
- linked crash taxonomy improvement for gate-edge/top collisions without losing
  passed-gate progress.

The final target remains:

- `success_rate >= 0.60`;
- `mean_time_s_success <= 7.0s`.

W&B reward curves are diagnostic only, not acceptance.

## Rollback

Rollback immediately if:

- hard eval remains `success_rate=0.0` and `mean_gates <= 0.9`;
- crash rate remains `1.0` with no linked gate-edge taxonomy improvement;
- W&B shows no gate/finish conversion;
- PPO instability appears severe enough to invalidate the run.

Do not continue from a failed reward-geometry checkpoint unless it becomes the
hard-eval best under the fixed inference path.

## Required Post-Run Analysis

After the train/eval chunk, run:

```text
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then review:

- evaluator summary;
- W&B gate/finish/crash curves;
- reward component balance;
- crash taxonomy for the best checkpoint if hard eval improves mean gates or
  changes target-gate crash distribution.

No second chunk may start before this analysis is written.
