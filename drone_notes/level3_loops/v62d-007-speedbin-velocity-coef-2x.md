# v62d_007：速度奖励加倍组合没有成功

这轮在做什么：

```text
speed_bin_balanced 轨迹生成器
+ command_vel_error_coef=1.2
```

通俗讲，就是一边让训练轨迹更强调不同速度段，一边再把“速度跟不上”的惩罚加重一点，看看 PPO tracker 会不会更听速度命令。

结果：没有达到预期。

最好的是 15M checkpoint：

```text
位置误差: 0.2026
横向轨迹误差: 0.1710
速度误差: 0.7943
done: 0.0
```

它的位置和轨迹跟踪比最老的 v62c 7M 好很多，但速度没有变好。和当前正式基线 v62c 7M 比，速度误差反而差了大约 7.4%。和之前的 v62d_004、v62d_006 比，也没有更好。

更重要的是，训练到后面会漂坏：

```text
15M 速度误差: 0.7943
30M/final 速度误差: 1.0491
```

这说明继续训这条路线不是好办法。它不是越训越稳，而是后面开始把速度控制训坏。

这轮也确认了一件事：action / logprob / tanh squashed Gaussian 这条路径是干净的，不是动作分布 bug。问题更像是行为学习本身：PPO 还是没有真正学会“同一条轨迹，不同速度命令就应该飞出不同速度”。

下一步应该换思路，不要继续简单加速度 reward。更合理的是做 v62d_008：

```text
velocity_contrast_constant_speed generator
```

也就是在训练数据生成器里系统性制造“速度对比”：

```text
差不多的轨迹
但有低速 / 中速 / 高速不同版本
并且有更长的恒速段
```

这样 PPO 才更难只靠追点混过去，必须真的读懂 desired_velocity 和 desired_speed。

当前结论：

```text
v62d_007 不晋级
不用 final checkpoint
不用继续 60M
下一步切回 generator distribution 方向
```
