# Level3 V49 Hidden512 Long-Horizon Baseline And Parameter Survey Plan

Status: approved structural plan for the next capacity-family baseline after
loop118/v48. Updated after user review: do not judge the larger network with a
5M short screen or by requiring it to immediately preserve the old 21% frontier.

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

No teacher, planner, shield, ensemble, waypoint controller, or upper-level
controller is allowed at inference.

## Investigation 1: Local Step-Curve Evidence

The Level2 step-curve packet is the strongest local reason to avoid a 5M or
30M pass/fail judgment.

`experiments/level3_ppo_loop/analysis/2026-06-18_level2_checkpoint_step_curve.md`
shows:

- `level2_DR_latencyobs_middlemanuever`: 30M had `0%` success, 45M jumped to
  `43%`, 70M first reached `66%`, and 95M peaked at `77%`.
- `level2_DR_latencyobs_middlemanuever_onemoretime`: 30M had only `2%`
  success, but 60M reached `75%` and final reached `80%`.

Implication: for a structurally changed Level3 policy, especially a wider
network that has to adapt newly expanded weights, 30M is diagnostic and 60M is
the first serious success-rate read. If W&B gate/finish signals or hard-eval
mean gates are still improving at 60M, continuing to 90M/120M is more justified
than abandoning the 512 family.

## Investigation 2: Current Level3 Plateau

Recent local Level3 evidence says small reward/contact tweaks are not opening a
new capability layer:

- loop107/v37 1M: `21%` success, `1.66` mean gates, `79%` crash.
- loop110/v39 3M: `21%` success, `1.64` mean gates, `79%` crash.
- loop116/v45: `20%` success, `1.60` mean gates, `80%` crash.
- loop117/v47: `20%` success, `1.58` mean gates, `80%` crash.
- loop118/v48: `16%` success, `1.50` mean gates, `84%` crash.

The immediate conclusion is not that 512 should beat 21% within a few million
steps. The more useful question is whether a 2x512 MLP can become a better base
for longer-horizon adaptation and later parameter, observation, memory, or
curriculum experiments.

Earlier hidden512 evidence from loop061 was negative, but it came from an older
loop052/v9 branch and reached only `10%` success. It does not answer whether
the current loop110/v39 3M v5 frontier benefits from a controlled 512-wide
warm-start plus a real long-horizon read.

## Investigation 3: External Architecture / Horizon Evidence

External sources do not prove that bigger is always better, but they do support
not dismissing a larger network from a short run:

- Stable-Baselines3 defaults are small for generic PPO: 1D PPO/A2C/DQN uses
  two fully connected layers with 64 units. This means our 2x256 is already
  larger than generic defaults, but generic defaults are not drone-racing
  evidence.
- The PPO implementation-details review reports the classic continuous-control
  PPO setup as a 2x64 Tanh MLP, and also emphasizes implementation details such
  as gradient clipping and diagnostic metrics. This supports using W&B/PPO
  health metrics rather than raw early success alone.
- Swift used PPO for drone racing with 2x128 policy/value networks, 100
  parallel agents, and `1e8` environment interactions. Its small network worked
  with a strong state representation, privileged Critic information, and a long
  training horizon.
- A quadrotor-control paper using differentiable simulation uses a 2-hidden-layer
  MLP with hidden size `512` for state-based control and `1024` for vision-based
  control, showing that 512-wide MLPs are reasonable in quadrotor policy work.
- CRL-Drone-Racing for obstacle-rich racing emphasizes multi-stage curriculum,
  domain randomization, and multi-scene updating for obstacle/gate tradeoffs.
  That suggests the 512 family should include later curriculum or distribution
  lanes, not only reward-number tweaks.

Sources:

- Stable-Baselines3 policy architecture docs:
  https://stable-baselines3.readthedocs.io/en/master/guide/custom_policy.html
- The 37 Implementation Details of PPO:
  https://iclr-blog-track.github.io/2022/03/25/ppo-implementation-details/
- Swift / champion-level drone racing:
  https://www.nature.com/articles/s41586-023-06419-4
- Learning Quadrotor Control From Visual Features Using Differentiable
  Simulation:
  https://arxiv.org/html/2410.15979v2
- CRL-Drone-Racing:
  https://github.com/SJTU-ViSYS-team/CRL-Drone-Racing

## V49 Hypothesis

```text
v49_v5_hidden512_mlp_warmstart_from_loop110_3m
```

A 2x256 v5 MLP may be too small or too brittle as the base policy for
Level3's randomized gates and obstacles. v49 isolates capacity first:

- same v5 observation;
- same v39 gate-acquisition reward numbers;
- same PPO rollout geometry;
- same hard eval on `config/level3.toml`;
- only change the Actor/Critic hidden width from `256` to `512`;
- warm-start from loop110/v39 3M using explicit block-copy expansion.

```text
loop110/v39 3M 2x256 MLP
  -> allow_hidden_dim_warmstart=True
  -> v49 2x512 MLP
```

## Training Lane

- Initial checkpoint: loop110/v39 3M MLP frontier.
- Train config: unchanged `config/level3.toml`.
- Hard eval config: unchanged `config/level3.toml`.
- Actor: v5 local-obstacle MLP, `mlp_2x_tanh`.
- Critic: same observation MLP.
- Hidden width: `512`.
- Retention: disabled.
- Reward structure: v39 `legacy_staged` gate-acquisition numbers.
- Horizon: one bounded `60M` long-horizon baseline.
- Checkpoints: `5M`, `10M`, `15M`, `20M`, `30M`, `45M`, `60M/final`.
- Step-curve maturation permission: enabled because the selected initial
  checkpoint, loop110/v39 3M, already has `21%` success and `1.64` mean gates
  on hard eval.
- W&B logging: required.

## Parameter Survey Matrix After V49

The next decision after v49 should be made from hard eval plus W&B curves.
Keep the Level3 track unchanged.

1. **If PPO movement is too weak**: approximate KL and clipfrac stay near zero,
   entropy is flat, and gate/finish signals do not move. Run a hidden512
   reward/PPO-number follow-up that increases update pressure, for example a
   slightly higher learning rate or lower entropy pressure, while keeping hard
   eval gates.
2. **If training is unstable**: value loss explodes, explained variance falls,
   tilt/crash rises, or success appears then disappears. Run a hidden512
   stability follow-up with lower learning rate, stronger gradient/tilt
   discipline, or retention/curriculum, chosen by the analysis packet.
3. **If gate phase confusion persists**: mean gates stays around 1.5-1.7 with
   seed churn and contact at gate 0/gate 2. Run a hidden512 observation,
   memory, or curriculum lane rather than another small reward-number tweak.
4. **If W&B and evaluator signals are still improving at 60M**: continue the
   same hidden512 hypothesis to 90M and possibly 120M with milestone selection.

## Promotion / Rejection Rule

Do not use 5M/10M/20M milestones as a pass/fail test against the old `21%`
frontier. They are learning-curve diagnostics.

For any lane that produces a `1M` checkpoint, that checkpoint is also only a
health check. The early checkpoints answer questions like:

- did the warm-start load correctly;
- are actions, observations, W&B, and checkpoint metadata sane;
- are KL, clipfrac, entropy, value loss, SPS, and gradients in a plausible
  range;
- did the policy catastrophically lose all basic gate progress;
- are mean gates, passed-gate rate, crash type, timeout, tilt, and seed churn
  changing in a diagnostically useful way.

They must not be used to require success-rate growth. In particular, do not
reject hidden512 because `1M`, `5M`, `10M`, `20M`, or `30M` fail to preserve or
beat the old `21%` frontier. The first serious success-rate exam for v49 is
the `60M` read, and a branch with improving signals at 60M should be considered
for `90M` or `120M`.

Promote early if any milestone shows one of:

- success `>21%`;
- success `>=21%` with mean gates above `1.66` and crash `<=79%`;
- clear success-seed expansion without losing the old frontier.

Continue toward 90M/120M if the 60M result has any of:

- non-zero success with mean gates near or above the old frontier;
- improving hard-eval mean gates across 30M/45M/60M;
- W&B gate/finish metrics still improving without PPO instability;
- new solved seeds that suggest the 512 policy is learning a different useful
  region of the validation distribution.

Hold for diagnosis, not family rejection, only if:

- success is near zero and mean gates stay `<0.50` across the long run;
- training/evaluation wiring fails;
- checkpoint warm-start metadata is inconsistent.

Do not reject the hidden512 family until at least three evaluated hidden512
family trials exist:

- the 60M hidden512 long baseline;
- one hidden512 reward/PPO-number follow-up;
- one hidden512 observation, memory, or curriculum follow-up.

## Next-Loop Requirement

After v49 completes, run `scripts/analyze_level3_ppo_trial.py`, spawn exactly
three review subagents for evaluator metrics, W&B/PPO diagnostics, and
structure/research synthesis, then write a main-agent decision packet before
any further hidden512 follow-up training. That packet should keep the next move
inside the hidden512 family unless v49 catastrophically loses basic gate
progress throughout the long run or exposes a wiring bug.
