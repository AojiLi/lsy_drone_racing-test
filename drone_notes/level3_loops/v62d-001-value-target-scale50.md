# v62d_001：value scale 让 critic 稳了，但没有让 tracker 变好

这轮做的是一个很窄的实验：

```text
不改 observation
不改 reward
不改 gate / obstacle / race 语义
只把 critic 要预测的 value target 缩小 50 倍
```

直觉是：之前 value loss 和 return scale 压力太大，可能影响 PPO 学速度控制。  
所以 v62d_001 想先把 critic 数值问题稳定下来。

结果分两半看。

好消息：

```text
value_loss 真的降下来了
explained_variance 到了 0.866
action/logprob 仍然是干净的
训练速度也很快，大约 1.0M steps/s
```

坏消息更关键：

```text
tracker 变成了“很会贴近轨迹，但不听速度”的策略
```

和 v62c 7M 比：

```text
v62c 7M velocity error: 0.7397
v62d_001 best velocity error: 1.2018

v62c 7M done: 0.00391
v62d_001 best done: 0.02903
```

也就是说，它的位置误差和 cross-track 变好了，但速度服从、稳定性、reward 都变差。

最好的 v62d_001 checkpoint 是：

```text
5M
lsy_drone_racing/control/checkpoints/v62d_001_value_target_scale50_30m/v62d_001_value_target_scale50_30m_step_005000000.pkl
```

但这个 checkpoint 不能提升为新 baseline。当前比较基线仍然是：

```text
v62c 7M
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

这轮最重要的发现是：

```text
value scale 可以修 critic 数值，
但不能自动修速度服从。
```

还有一个干扰变量：v62d_001 比 v62c 的 PPO 更新更激进。

```text
v62c: 4 minibatches, 1 update epoch
v62d_001: 8 minibatches, 4 update epochs
```

所以下一步不应该马上改 reward。更合理的是先跑：

```text
v62d_002_value_scale50_conservative_ppo
```

也就是保留 value scale，但把 PPO 更新强度降回 v62c 风格，看看速度崩坏是不是因为更新太猛。如果还崩，再去调“通用速度服从 reward”，但仍然不能加 gate reward。
