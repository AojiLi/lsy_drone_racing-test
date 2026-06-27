# v62c 10M 训练结果

这次跑的是：

```text
v62c_tanh_squashed_gaussian_10m
10,027,008 steps
1024 envs x 32 steps
```

W&B：

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62c_tanh_squashed_gaussian_10m_20260627
```

## 最重要结论

**JAX/v62c 能学。**

这次不是完全成功，但它已经能说明：

```text
JAX trainer 不是明显坏的
tanh-squashed Gaussian 也不是问题
action/logprob 账本是干净的
```

## 好消息

pre/post eval 变好了：

```text
reward: -4.667 -> -3.038
position error: 0.499 -> 0.444
cross-track error: 0.412 -> 0.325
done mean: 0.0064 -> 0
```

动作分布也很干净：

```text
action clip fraction = 0
logprob/env consistency error ≈ 3e-7
post-audit action_sampling_logprob = ok
post-audit advantage_scale = ok
```

速度也很快：

```text
steady-state ≈ 1.305M env steps/s
约等于 PyTorch fast path 的 32.8 倍
```

## 问题

速度跟踪变差：

```text
velocity error: 0.607 -> 0.746
```

动作更大，动作变化也更大：

```text
action_abs_mean 上升
action_delta_penalty 上升
```

训练最后的 value 压力还是明显：

```text
value loss = 1766
advantage mean/std = -41.87 / 42.29
```

通俗说：

```text
PPO 开始学会贴近轨迹
但还没有很好地学会“按速度跟轨迹”
critic/value 还有点吃力
```

## 当前判断

这次可以基本排除：

```text
JAX 完全不能学
tanh action 分布有大错
logprob 账本不一致
```

但不能直接开 60M+。

下一步应该先看：

```text
1M / 2M / ... / 9M / final 哪个 checkpoint 最好
velocity error 是不是中途更好、后面变差
value loss / advantage 是不是长期偏大
```

一句话：

**v62c 路线能走，但下一步要先做 milestone + value/velocity review，而不是马上长训。**
