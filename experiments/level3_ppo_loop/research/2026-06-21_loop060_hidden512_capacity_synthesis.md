# Loop060 Hidden512 Capacity Synthesis

## Question

After loop060, should the Level3 loop test a larger PPO policy/value network?

## Local Evidence

- Target remains hard eval on `config/level3_dr.toml`; the Level3 track must not
  be modified.
- Current best remains loop052: success rate 20%, crash rate 80%, mean
  successful time 6.975s, mean gates 1.4.
- loop060 added v9 gate-aperture-margin observation features and warm-started
  from loop052, but the best hard-eval checkpoint reached only 15% success,
  85% crash, and mean gates 1.3.
- loop060 W&B diagnostics showed very low PPO movement: approx_kl and clipfrac
  stayed near zero while gate/finish rates stayed flat. The added features did
  not convert into hard-eval progress with the existing 2x256 Tanh MLP.
- The loop052 checkpoint has hidden_dim=256 and about 168k policy/value
  parameters for the v5 observation layout. The v9 observation adds geometric
  features, but the network remains a small two-hidden-layer actor and critic.

## External Evidence

- PPO continuous-control defaults are often smaller than this project's current
  network. The original PPO MuJoCo setup and Stable-Baselines3 defaults use
  two hidden layers with 64 units, so 2x256 is not obviously undersized by
  generic PPO standards.
- Drone-racing references do not prove that 2x256 is insufficient. Swift and
  related racing policies often use compact feed-forward MLPs, and their
  performance depends heavily on observation design, reward, curriculum, and
  initialization.
- Larger networks are nevertheless normal in harder robotics/racing settings.
  CRL-Drone-Racing uses policy/value heads shaped around 512 and 256 units, and
  IsaacGym/IsaacLab locomotion and quadrotor examples commonly use tapered MLPs
  such as 512/256/128 or 256/256/128.
- The most relevant capacity test for this codebase is not recurrent policy or
  attention yet. The current observation already includes short history and
  fixed local obstacle features. A recurrent or attention lane would change
  more variables and require broader checkpoint metadata changes.

## Recommendation

Run one named capacity structural lane before more reward-only tuning:

- Lane name: `v10_hidden512_warmstart_capacity_from_loop052`
- Keep the Level3 target track unchanged.
- Keep v9 observation, current reward scale, controller settings, PPO settings,
  and 30M screening horizon.
- Widen the actor and critic 2-layer Tanh MLP from hidden_dim=256 to
  hidden_dim=512.
- Warm-start from loop052 with explicit block-copy expansion rather than
  starting from scratch. This preserves known Level3 flight behavior while
  testing whether the wider network can use the v9 aperture-margin features.
- Evaluate 5M-step milestones plus the final checkpoint. If success exceeds
  loop052's 20% or mean gates materially exceeds 1.4, mature the same lane
  toward 60M before rejecting it.

## Sources

- PPO paper: https://arxiv.org/abs/1707.06347
- Stable-Baselines3 custom policy defaults:
  https://stable-baselines3.readthedocs.io/en/master/guide/custom_policy.html
- What Matters for On-Policy Deep Actor-Critic Methods:
  https://openreview.net/forum?id=nIAxjsniDzg
- Swift drone racing: https://www.nature.com/articles/s41586-023-06419-4
- CRL-Drone-Racing: https://github.com/SJTU-ViSYS-team/CRL-Drone-Racing
- IsaacGymEnvs Quadcopter PPO:
  https://github.com/isaac-sim/IsaacGymEnvs/blob/main/isaacgymenvs/cfg/train/QuadcopterPPO.yaml
- IsaacLab task configs: https://github.com/isaac-sim/IsaacLab
