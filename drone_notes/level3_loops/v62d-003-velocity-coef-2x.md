# v62d_003：速度奖励加倍，效果不够

这轮做的是：

```text
不改赛道
不加过门奖励
不加 gate/obstacle 输入
只把底层 tracker 的速度误差奖励加重
```

具体改动是：

```text
vel_error_coef: 0.6 -> 1.2
```

想验证的问题很简单：

```text
PPO tracker 是不是只是“不够重视 desired_velocity / desired_speed”？
```

训练已经从零跑完 `30M`，并评估了：

```text
5M / 10M / 15M / 20M / 25M / 30M / final
```

## 最好的 checkpoint

这轮最好的点是：

```text
20M
lsy_drone_racing/control/checkpoints/v62d_003_velocity_coef_2x_30m/v62d_003_velocity_coef_2x_30m_step_020000000.pkl
```

但它没有超过 v62c 7M 基线。

和 v62c 7M 比：

```text
位置误差：0.6573 -> 0.6381，稍微变好
横向误差：0.5214 -> 0.5022，稍微变好
速度误差：0.7397 -> 0.7219，只好 2.4%
done：不变
动作变化：差了约 7.9 倍
```

所以通俗讲：

```text
它确实稍微更听速度命令了，
但进步太小，而且动作更抖/更不平滑。
```

## 这说明什么

这轮不是 JAX 或 tanh action 出问题。

审计结果是干净的：

```text
action/logprob 正确
没有 action clipping
advantage scale 正常
reward scale 正常
```

更像是：

```text
光把速度奖励加大，不足以让 PPO 真正学会“按速度命令飞”。
```

PPO 可能需要在训练数据里看到更清楚的例子：

```text
匀速飞
提前减速
慢速穿过
恢复速度
停住/悬停
```

也就是说，下一步不应该继续粗暴加 reward 系数，而应该改 reference
generator，让它生成更清楚、更平衡的速度训练分布。

## 下一步

下一轮建议是：

```text
v62d_004_speed_bin_balanced_generator
```

核心想法：

```text
不是继续告诉 PPO “速度错了扣更多分”，
而是在训练里给它更多明确的速度场景：
该匀速就匀速，
该减速就提前减速，
该低速通过就低速通过，
该恢复就平滑恢复。
```

这轮 `v62d_003` 不晋级。当前 frontier 仍然是：

```text
v62c 7M
```
