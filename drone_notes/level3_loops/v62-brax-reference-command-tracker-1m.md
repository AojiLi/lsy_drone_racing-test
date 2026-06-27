# v62 Brax Reference Command Tracker 1M 记录

这次做了两件事：

```text
1. 把 v62 从 smoke 脚本升级成正式 lane
2. 跑了一个 1M steps 的 bounded learning-signal run
```

正式 lane 是：

```text
v62_brax_reference_command_tracker
```

新入口是：

```text
scripts/train_v62_brax_reference_command_tracker.py
```

它现在能做：

```text
JAX policy
JAX rollout
GAE
PPO update
milestone checkpoint
final checkpoint
W&B offline log
训练前 eval
训练后 eval
eval delta 对比
```

## 结论 1：速度很好

1M run 用的是：

```text
1024 envs x 32 steps
32 个 PPO update
总步数 1,048,576
```

前两轮还是编译，所以慢。编译之后速度稳定在：

```text
大约 1.15M - 1.36M env steps/s
```

最终 summary：

```text
steady_state_steps_per_s = 1.3047M
相对 PyTorch fast path = 32.78 倍
```

所以从“训练效率”角度看，Brax/JAX 这条路是对的。

## 结论 2：PPO 没有数值爆炸

训练过程中：

```text
all_finite = 1.0
final KL = 0.000248
final clip_fraction = 0.0
entropy 大概 3.68 -> 3.70
```

这说明它不是 NaN，也不是 KL 爆炸。

但也有明显问题：

```text
value_loss 很大，最后 6502
grad_norm 很大，最后 641
rollout tracking error 后面变大
```

所以它“能跑”，但还不是“学得好”。

## 结论 3：eval 没有正向学习信号

训练前 eval：

```text
reward_mean = -3.3313
position_error = 0.5496
velocity_error = 0.6065
cross_track_error = 0.4548
```

训练后 eval：

```text
reward_mean = -7.2119
position_error = 0.6459
velocity_error = 1.5760
cross_track_error = 0.5189
```

也就是说：

```text
训练后反而更差
```

脚本判断也是：

```text
has_eval_learning_signal = false
```

## 通俗解释

现在的情况像是：

```text
发动机很强，传动系统也接上了，
但车手训练方向不对，越练动作越大，跟踪反而变差。
```

所以现在不能直接开 8M 或 20M 长训。

下一步应该做：

```text
v62b learning-signal fix
```

优先怀疑：

```text
探索太大
动作采样和动作裁剪有 mismatch
reward/value scale 太大
critic 学得吃力
```

更具体的下一步：

```text
降低 initial_log_std
降低或关闭 ent_coef
考虑 squashed-action PPO logprob
加 reward scaling / return normalization
再跑同样的 1M learning-signal gate
```

这次没有改 `config/level3.toml`，也没有加入 gate reward。
