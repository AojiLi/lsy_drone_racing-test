# v55 multi_point_reference attempt001 做了什么

这一轮通过了第七关：`multi_point_reference`。

这一关的意思是：

```text
不是只跟一个点
而是给 PPO 一串 reference points
看它能不能一个一个平滑切过去
```

为什么重要：

```text
以后 planner 给底层 PPO 的就会是一串局部目标点
所以 PPO 必须会“切点”
不能到一个点就冲过头
也不能每切一次点动作大幅抖动
```

训练方式：

```text
从 heading_tracking 通过的 checkpoint 继续
1024 个并行环境
总共 8M steps
每 1M 保存一个 checkpoint
```

最好的通过点是 1M checkpoint，不是 final：

```text
segment completion: 100%
crash: 0%
平均位置误差: 约 0.178m
p90 位置误差: 约 0.279m
切点 overshoot: 约 0.0046m
动作变化: 很小
```

后面的 checkpoint 有些平均误差更好，但 p90 误差和动作变化变差，说明继续训不一定更稳。

通俗讲：底层 tracker 已经会跟一串点走，但目前最好状态出现在早期。下一关是 `l_shape_tracking`，也就是让它跟一个带拐角的 L 形轨迹。
