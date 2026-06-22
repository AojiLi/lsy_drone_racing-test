# Level3 Recurrent Actor GRU-256 Strategy

## Question

After retaining the current 2x256 MLP baseline and testing hidden512 as a cheap
capacity ablation, what is the next structural lane that best matches the
Level3 failure mode?

## Local Evidence

- Current best hard-eval checkpoint remains loop052:
  - success_rate: 0.20
  - crash_rate: 0.80
  - mean_gates: 1.4
  - mean successful time: 6.975s
  - observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
  - network: 2x256 Tanh MLP Actor and 2x256 Tanh MLP Critic
- Loop060 added v9 gate-aperture-margin observation features but did not beat
  loop052: best success_rate was 0.15 with mean_gates 1.3.
- The target metric is not mainly speed. Successful episodes already average
  under 7.0s. The deficit is stable gate acquisition, obstacle avoidance, and
  full-race completion.
- The v5 observation is local and compact: vehicle state, current target gate,
  another relevant gate, two nearby obstacles, previous action, and two steps
  of manual history. That makes the task partially observable rather than a
  pure single-frame mapping problem.

## Interpretation

Pure MLP widening can improve function approximation but does not directly
address temporal aliasing. Level3 randomizes gate and obstacle geometry, and
local observations can be ambiguous without recent motion context. A recurrent
Actor can learn approach direction, obstacle-relative motion, gate-side entry
history, and recovery dynamics over roughly 0.3-0.6 seconds.

The first recurrent experiment should isolate memory. Do not combine GRU,
privileged Critic, reward redesign, and observation changes in one step.

## Recommended Lane

Use a named structural lane:

`v11_recurrent_actor_gru256_screen_from_scratch`

Architecture:

- Actor observation: v5 68-dim local-obstacle observation.
- Actor:
  - FC 128 + Tanh
  - FC 128 + Tanh
  - GRU 256
  - FC 192 + Tanh
  - FC 96 + Tanh
  - Action Mean 4 + Tanh
  - independent learned log_std[4]
- Critic, first screen:
  - same actor observation, not privileged state yet
  - FC 256 + Tanh
  - FC 256 + Tanh
  - Value 1
- Sequence length: 32 steps at 50 Hz, about 0.64s.
- Reset GRU hidden state on episode termination/truncation.
- Hard eval: unchanged `config/level3_dr.toml`.

## Why Not Privileged Critic First

Privileged Critic is plausible and likely valuable, but it changes value-target
learning and rollout storage at the same time as recurrent policy learning.
The safer sequence is:

1. Validate recurrent Actor with same-observation Critic.
2. If hard eval shows non-zero success or mean_gates improvement, mature it to
   60M-90M.
3. Only then test a second named lane with privileged Critic.

## Implementation Gate

This lane must not be launched by the current trainer until recurrent PPO
support exists. Required implementation work:

- rollout buffer stores GRU hidden states and done masks;
- PPO update batches contiguous sequences rather than fully shuffled single
  transitions;
- hidden state resets on episode boundaries;
- checkpoint metadata records policy architecture and recurrent dimensions;
- `ppo_level3_inference.py` maintains deterministic GRU hidden state during
  hard evaluation;
- analyzer/W&B metadata records the training structure.

