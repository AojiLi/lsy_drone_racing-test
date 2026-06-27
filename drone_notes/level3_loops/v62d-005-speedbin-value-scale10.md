# v62d-005：value scale 这轮说明了什么

这轮还是在训练底层 PPO tracker，不是 Level3 正赛。

目标是看一个问题：

```text
保留 v62d_004 里比较有用的 speed_bin_balanced 训练分布，
再把 value_target_scale 改成 10，
能不能让训练后期不漂、速度跟踪更稳？
```

结果：不能。

最好的是 15M checkpoint：

```text
lsy_drone_racing/control/checkpoints/v62d_005_speedbin_value_scale10_30m/v62d_005_speedbin_value_scale10_30m_step_015000000.pkl
```

它的好处：

```text
位置误差小
横向误差小
critic/value 指标比之前健康
```

但关键问题更严重：

```text
速度误差很差
动作幅度明显变大
动作变化非常不平滑
final 比 15M 更差
```

通俗说：

```text
value scale 让 critic 的账本更好看，
但没有让飞机更听“按这个速度飞”的命令。
```

而且它有点变成：

```text
为了追上轨迹，动作更猛，
速度不听话，
稳定性变差。
```

所以 v62d_005 不晋级。

下一步建议是 v62d_006：

```text
不要继续调 value scale
不要马上改 reward
保留 speed_bin_balanced
把 rollout 从 1024 envs x 32 steps
改成 256 envs x 128 steps
```

原因是 tracker 需要学会：

```text
提前减速
停住/保持
低速穿过
再慢慢恢复速度
```

这些行为跨越的时间可能比 32 step 更长。换成 128 step，可以让 PPO 在一次
rollout 里看到更完整的动作后果。

这仍然不改 Level3 赛道，也不加过门奖励。

