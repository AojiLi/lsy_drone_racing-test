# v62b 10M 训练结果

这次做的是一个很窄的 PPO 修复，不是调 reward。

之前的问题是：

```text
PPO 采样出来一个 action
环境实际执行的是 clip 后的 action
但 PPO 训练时算的是原始 action 的 logprob
```

也就是 PPO 以为自己做了 A，环境实际做了 B。这个会污染训练。

这次已经改成：

```text
环境执行哪个 action
PPO batch 里就存哪个 action
logprob 也按这个 action 算
```

同时：

```text
initial_log_std 默认从 -0.5 改成 -2.0
entropy pressure 默认从 0.01 改成 0.0
```

## 10M 结果

这次实际跑了：

```text
10,027,008 steps
1024 envs x 32 steps
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62b_brax_ppo_signal_fix_10m_20260627
```

速度还是很快：

```text
steady-state 约 1.30M env steps/s
约等于 PyTorch fast path 的 32.6 倍
```

## 好消息

PPO 信号问题修掉了：

```text
action clip fraction = 0
logprob/env action consistency error = 0
final checkpoint std = 0.1315
final checkpoint audit 全部通过
```

pre/post eval 也变好了：

```text
reward: -4.109 -> -2.741
position error: 0.515 -> 0.401
cross-track error: 0.435 -> 0.280
done mean: 0.00417 -> 0
```

这说明 v62b 不是白跑，确实开始学到了东西。

## 还没好的地方

速度跟踪变差了：

```text
velocity error: 0.548 -> 0.681
```

训练最后的 value/advantage 压力也还大：

```text
advantage mean/std = -46.06 / 42.59
value loss = 1962
```

通俗说：

```text
飞机更会贴着轨迹走了
但速度控制还不够好
critic/value 还在吃力
```

## 当前判断

这次 v62b fix 是有效的。

但下一步不要马上调 reward。更稳的是先看：

```text
1M / 2M / ... / 9M / final 哪个 checkpoint 最好
W&B 上 velocity error 是怎么变化的
value loss 和 advantage 是不是一直偏大
```

如果只是 final 速度变差，也许中间某个 checkpoint 更好。  
如果所有 checkpoint 都有 value/advantage 压力，再考虑 value normalization
或者 critic target scaling。

一句话：

**现在 PPO 终于在学了，下一步先选好 checkpoint、看 value 问题，再考虑 reward。**
