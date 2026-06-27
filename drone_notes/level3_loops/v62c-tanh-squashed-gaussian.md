# v62c：正式采用 tanh-squashed Gaussian

这次不是在调 reward，也不是在改赛道。

这次解决的是 PPO 动作分布的“账本”问题。

之前 v62b 是一个快速止血方案：

```text
采样 Gaussian action
超过 [-1, 1] 就 clip
尽量把 std 调小，让 clip 少发生
```

它能验证学习信号，但长期看不够正式。因为 clip 本身不是一个干净的概率变换。

现在 v62c 改成：

```text
先采样 raw_action
再用 tanh(raw_action) 得到真正执行的 env_action
logprob 也按 tanh 变换修正
```

通俗说就是：

```text
动作天然不会超界
PPO 知道自己真正执行了什么
训练账本和环境动作对得上
```

## 这次验证结果

smoke 里确认：

```text
action_distribution = tanh_squashed_gaussian
action_logprob_mode = tanh_squashed_gaussian_logprob_with_jacobian
action clip fraction = 0
logprob/env consistency error ≈ 3.18e-7
all_finite = 1
```

审计里确认：

```text
action_clipping = ok
action_sampling_logprob = ok
stored-vs-env logprob abs mean ≈ 3.21e-7
```

这说明 B 方案的关键实现是对的。

## 还要注意什么

advantage scale 还是偏大，这是 v62b 就存在的问题，不是 tanh 方案新引入的问题。

所以接下来不要直接 100M 长训。更合理的是先跑一个：

```text
v62c_tanh_squashed_gaussian_10m
```

然后看：

```text
reward 有没有继续改善
position/cross-track error 有没有下降
velocity error 有没有恶化
value loss / advantage scale 是否还很大
中间 checkpoint 是否比 final 更好
```

一句话：

**B 方案现在已经接上了，下一步可以用它跑 bounded 10M 正式训练；但长训前还要看 value/velocity 这些诊断。**
