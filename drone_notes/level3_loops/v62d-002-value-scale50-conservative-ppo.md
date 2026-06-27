# v62d_002 结果：保守 PPO 没有救回速度问题

这轮做的是 v62d_002：

```text
value_target_scale = 50
num_minibatches = 4
update_epochs = 1
从零训练 30M
```

它的目的很窄：验证 v62d_001 失败是不是因为 PPO 更新太猛。v62d_001 同时改了 value scale 和 PPO 更新压力，所以这轮把 PPO 更新方式改回更保守的 v62c 风格。

结论：v62d_002 比 v62d_001 好，但没有超过 v62c 7M。

最好 checkpoint 是 5M：

```text
lsy_drone_racing/control/checkpoints/v62d_002_value_scale50_conservative_ppo_30m/v62d_002_value_scale50_conservative_ppo_30m_step_005000000.pkl
```

和 v62c 7M 对比：

| 指标 | v62c 7M | v62d_002 5M |
|---|---:|---:|
| reward | -4.8459 | -6.9258 |
| 位置误差 | 0.6573 | 0.4066 |
| 轨迹横向误差 | 0.5214 | 0.3439 |
| 速度误差 | 0.7397 | 0.7721 |
| done | 0.00391 | 0.01615 |
| action delta | 0.000006 | 0.00276 |

通俗讲：

```text
它更会贴近轨迹了，
但是速度听话程度更差，
动作也更不平滑，
更容易提前 done。
```

所以它不能晋级。

更重要的判断是：value scale 这条线可以先放下。审计显示 action/logprob 没坏，critic scale 也被修好了，但 policy 还是变成“追点追得更猛”的行为。也就是说，核心问题不是 JAX 后端，也不是 tanh action，也不只是 critic 数值尺度。

下一步应该切到通用速度服从 reward：

```text
v62d_003_velocity_coef_2x
```

只改一个通用 tracker reward 数字：

```text
vel_error_coef: 0.6 -> 1.2
```

这个不是 gate reward，不是过门奖励，也不是 Level3 赛道作弊。它只是让底层 tracker 更重视：

```text
planner 叫你多快，你就多快
该慢就慢
该刹就刹
不要只顾贴近参考点
```

下一轮训练前需要 builder/checker，因为 reward 数字变了。Level3 赛道和 tracker free-space config 都不能改。
