# v62d-004：速度分箱 generator 这轮做了什么

这轮不是在跑 Level3 正赛，而是在训练底层 PPO tracker：

```text
给它一段 reference 小轨迹
让它学会稳、准、按速度跟过去
```

v62d_004 改的是训练数据的分布。之前 reference 里的速度变化不够明确，
所以这轮让 generator 更频繁地产生这些情况：

```text
正常通过
提前减速
低速通过
恢复速度
停住/保持
```

结果很有信息量，但不能 promote。

最好的是 5M checkpoint：

```text
lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m/v62d_004_speed_bin_balanced_generator_30m_step_005000000.pkl
```

它的好处：

```text
位置误差和横向误差明显变小
done = 0
动作/logprob 没问题
```

问题：

```text
速度误差没有达到要求
5M 之后越训越差
动作平滑性变差
critic/value 还是学得很差
```

最关键的一句话：

```text
这轮说明“训练分布”方向有用，但单靠 speed-bin generator 不够。
```

下一轮建议是 v62d_005：

```text
保留 speed_bin_balanced
把 value_target_scale 改成 10
看能不能减少 5M 之后的漂移
```

这不是改赛道，也不是加过门奖励；还是在训练一个干净的底层 tracker。
