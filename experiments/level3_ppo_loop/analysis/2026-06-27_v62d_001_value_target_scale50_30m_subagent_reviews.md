# v62d_001 Subagent Reviews

Date: 2026-06-27

## tracker_eval_metrics

Verdict: do not promote `v62d_001`.

Best checkpoint by balanced score:

```text
lsy_drone_racing/control/checkpoints/v62d_001_value_target_scale50_30m/v62d_001_value_target_scale50_30m_step_005000000.pkl
```

Metrics:

```text
reward: -9.7541
balanced: -11.9443
position error: 0.2851
cross-track: 0.2633
velocity error: 1.2018
done mean: 0.02903
action delta: 0.01675
```

Against the v62c 7M baseline, this fails promotion. v62c 7M had reward
`-4.8459`, balanced `-7.5365`, velocity `0.7397`, done `0.00391`, and action
delta about `6.39e-6`.

The failure mode is behavioral, not action-path plumbing: spatial metrics got
much better, but velocity, done rate, reward, and smoothness got much worse.

## tracker_wandb_ppo

Value/critic stabilization worked:

```text
final value_loss: 0.0006676
final explained_variance: 0.8662
final raw advantage mean/std: -0.1336 / 1.8043
best audit advantage_scale: ok
```

Action/logprob path remained healthy:

```text
action clipping: 0.0
any-dim clipping: 0.0
final stored-vs-env logprob consistency: 3.31e-6
best audit stored-vs-env abs mean: 9.04e-7
```

But PPO behavior drifted:

```text
final approx_kl: 0.02150
max approx_kl: 0.03399
final clip_fraction: 0.2741
max clip_fraction: 0.3325
entropy: -2.3299 -> -5.9083
final action_abs_mean: about 0.512
```

Final eval improved position/cross-track but regressed the core blocker:

```text
position: 0.8173 -> 0.2576
cross-track: 0.6924 -> 0.2412
velocity: 0.6234 -> 1.3394
reward: -5.5937 -> -10.9498
done: 0.00441 -> 0.03403
```

## tracker_structure_research

Recommendation: do not switch directly to reward/generator changes yet. The
run changed both value scaling and PPO update pressure:

```text
v62c: 4 minibatches, 1 update epoch
v62d_001: 8 minibatches, 4 update epochs
```

Because critic scale now looks healthy but policy update pressure is elevated,
the next candidate should isolate a PPO-stabilizer/conservative-update test:

```text
candidate: v62d_002_value_scale50_conservative_ppo_10m
keep: value_target_scale=50.0
change: --num-minibatches 4 --update-epochs 1
```

If conservative PPO still trades velocity away, then v62d_003 should move to
generic velocity-obedience reward numbers, such as strengthening desired
velocity/along-speed terms. That follow-up must remain generic: no gate,
aperture, race, finish, or stage reward.

