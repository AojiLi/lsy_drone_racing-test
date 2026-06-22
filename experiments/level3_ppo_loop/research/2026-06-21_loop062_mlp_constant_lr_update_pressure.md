# Loop062 MLP Constant-LR Update Pressure Synthesis

## Question

After `v11_recurrent_actor_gru256_screen_from_scratch` failed, what is the
lowest-risk next experiment that still addresses a real observed failure mode?

## Local Evidence

Loop062 GRU screen:

- Best hard-eval checkpoint: 10M.
- Success rate: 0.00.
- Mean gates: 0.10.
- Crash rate: 0.55.
- Timeout rate: 0.45.
- Later 15M, 20M, 25M, and final checkpoints all had 0.00 mean gates.
- W&B showed no conversion: `race/passed_gate_rate = 0.0` and
  `race/finished_rate = 0.0`.
- PPO update pressure was very low: tail `approx_kl` was about `1.2e-5`,
  `clipfrac = 0.0`, and the final learning rate annealed to near zero.

Global best remains loop052:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Network:
  2x256 Tanh MLP Actor/Critic
- Success rate: 0.20.
- Mean gates: 1.40.
- Mean successful time: 6.975s.
- Crash rate: 0.80.

Previous loop052 follow-ups tried more nominal training, mild gate pressure,
PPO update pressure with LR annealing, soft centerline shaping, low entropy,
observation changes, hidden512, and GRU. None beat loop052.

## Interpretation

Loop062 should not be matured. It has no hard-eval success and no meaningful
gate progress. The GRU idea is not globally rejected, but this configured
from-scratch GRU screen is rejected.

The lowest-risk next experiment is to return to the only checkpoint with real
Level3 competence, loop052, and isolate one training-number variable that
previous loop052 fine-tunes did not isolate: learning-rate annealing.

The hypothesis is not that constant LR solves Level3 by itself. The hypothesis
is narrower: previous fine-tunes may have lost useful update pressure late in
the run, while hard eval still needs a checkpoint selected from the trajectory.
A short constant-LR fine-tune from loop052 can test this without changing the
observation layout, reward structure, reward numbers, controller, network
width, algorithm, or target track.

## Recommended Lane

Use a named lane:

`v12_mlp_loop052_constant_lr_nominal_reward`

Contract:

- Initial checkpoint: loop052 final.
- Observation: v5 local-obstacle observation.
- Actor/Critic: existing 2x256 Tanh MLP.
- Reward numbers: same nominal loop052 scale.
- PPO/training numbers: same as loop052 nominal fine-tune except
  `anneal_lr=False`.
- Training horizon: 20M screening, with 5M checkpoint interval.
- Hard eval: unchanged `config/level3_dr.toml`.

Promotion rule:

- If success rate exceeds loop052's 0.20 or mean_gates materially exceeds 1.40,
  continue the same hypothesis toward 60M/90M.
- If it fails, reject constant-LR fine-tuning and do not rerun the same MLP
  lane with only cosmetic reward changes.

