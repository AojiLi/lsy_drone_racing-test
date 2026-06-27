# v62d_008 这一轮做了什么

这一轮不是在跑 Level3 完赛，而是在训练底层 PPO tracker：

```text
planner 给一小段 reference 轨迹
PPO tracker 负责稳、准、按速度跟过去
```

这次尝试的核心叫：

```text
velocity_contrast_constant_speed
```

通俗说，就是训练时故意让相似的轨迹出现不同速度版本：

```text
同样差不多的路线
有时候要求慢
有时候要求中速
有时候要求快
```

这样 PPO 不能只靠“追点”，必须真的看懂：

```text
desired_velocity / desired_speed 到底让我飞多快
```

## 结果

最好的 checkpoint 是 30M：

```text
lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_generator_30m/v62d_008_velocity_contrast_constant_speed_generator_30m_step_030000000.pkl
```

和 v62c 7M baseline 对比：

| 指标 | v62c 7M | v62d_008 30M | 变化 |
|---|---:|---:|---|
| velocity error | 0.7397 | 0.5708 | 明显更好，提升 22.8% |
| position error | 0.6573 | 0.7943 | 变差 20.8% |
| cross-track | 0.5214 | 0.5449 | 变差 4.5% |
| done mean | 0.00391 | 0.00219 | 更好 |

这说明：

```text
这招真的让 PPO 更听速度指令了
但它为了听速度，牺牲了位置/轨迹精度
```

也就是说，它不是没用，反而很关键：它第一次明显打开了“速度服从”这个能力。

## 为什么不直接晋级

因为当前 goal 里的晋级规则不是只看速度：

```text
速度要提升 10%-15%
位置和 cross-track 不能变差超过 5%
```

v62d_008 的速度提升够了，但 position error 变差 20.8%，所以不能作为新的完整 best tracker。

## 下一步

下一轮应该做：

```text
v62d_009_velocity_contrast_spatial_guarded_generator
```

意思是：

```text
保留 v62d_008 的速度对比训练
但把轨迹距离、减速位置、空间约束调得更保守
让 PPO 既听速度，也别飞散
```

一句话：

```text
v62d_008 证明了“速度指令能学会”；
v62d_009 要解决“学速度时别丢掉轨迹精度”。
```
