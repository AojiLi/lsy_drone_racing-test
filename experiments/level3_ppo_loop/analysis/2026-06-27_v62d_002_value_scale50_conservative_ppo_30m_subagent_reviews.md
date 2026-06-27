# v62d_002 Subagent Reviews

Date: 2026-06-27

## tracker_eval_metrics

Best v62d_002 checkpoint:

```text
5M
lsy_drone_racing/control/checkpoints/v62d_002_value_scale50_conservative_ppo_30m/v62d_002_value_scale50_conservative_ppo_30m_step_005000000.pkl
```

It is best by balanced score and least-bad velocity behavior:

```text
reward: -6.9258
position error: 0.4066
cross-track: 0.3439
velocity error: 0.7721
done: 0.01615
action delta: 0.00276
balanced: -9.0010
```

Promotion verdict: fail. The checkpoint improves position and cross-track
versus v62c 7M, but it is worse on velocity, done rate, action delta, reward,
and balanced score.

Most likely behavior failure: spatial tracking over speed-command obedience.
The policy learns to chase the reference geometry more closely, but not to obey
desired speed/slowdown commands smoothly.

Recommendation: reject v62d_002. Move away from pure value-scale or
PPO-stabilizer candidates and target generic velocity-obedience reward balance.

## tracker_wandb_ppo

The local summary and audit were used; W&B history was not queried.

Action path verdict: healthy. The v62d_002 best checkpoint has:

```text
action_clipping: ok
action_sampling_logprob: ok
any_dim_clipped_fraction: 0.0
stored-vs-env logprob abs mean: 7.1e-7
policy std mean: 0.1336
```

Value scale verdict: `value_target_scale=50.0` fixed the critic scale under
conservative PPO. Final values and targets are aligned:

```text
value_loss: 0.0221
raw values_mean: -265.27
returns_mean: -265.40
scaled values_mean: -5.305
value_targets_mean: -5.308
```

Remaining PPO concern: final KL/clip remains high:

```text
v62d_002 final approx_kl / clip_fraction: 0.0210 / 0.2786
v62d_001 final approx_kl / clip_fraction: 0.0215 / 0.2741
v62c final approx_kl / clip_fraction: about 0.00369 / 0.0402
```

Behavior failure remains velocity/action/done drift:

```text
position improves: 1.115 -> 0.376
cross-track improves: 0.786 -> 0.320
velocity worsens: 0.647 -> 1.242
done worsens: 0.0029 -> 0.0254
action_abs rises: 0.016 -> 0.304
reward worsens: -6.21 -> -9.47
```

Recommendation: do not promote and do not run 60M+ maturation. Treat value
scaling as solved enough, and next adjust generic desired-velocity obedience,
action magnitude/delta cost, and/or KL pressure.

## tracker_structure_research

The value-scale isolation question should be closed. Restoring conservative PPO
update pressure did not rescue `value_target_scale=50.0`:

```text
v62d_002 5M velocity error: 0.7721
v62c 7M velocity error: 0.7397
v62d_002 5M done mean: 0.0162
v62c 7M done mean: 0.0039
```

Next candidate family: Family B, velocity obedience reward numbers.

Recommended single knob for `v62d_003`:

```text
ReferenceCommandReward vel_error_coef: 0.6 -> 1.2
```

Recommended baseline settings:

```text
value_target_scale=1.0
num_minibatches=4
update_epochs=1
1024 envs x 32 steps
tanh_squashed_gaussian
train from scratch
```

This remains generic tracker training because it only strengthens desired
velocity matching for the existing dense command horizon. It does not add
gate/aperture/race/finish/stage reward, and it does not add gate, obstacle, or
planner-phase actor inputs.

Recommendation: continue with another 30M from-scratch candidate after
builder/checker validation. No hold is needed yet.
