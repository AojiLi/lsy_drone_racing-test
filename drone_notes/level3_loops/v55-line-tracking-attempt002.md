# v55 line_tracking attempt002 做了什么

这一轮通过了第五关：`line_tracking`。

先修了上一轮发现的语义问题：

```text
直线轨迹走到终点后
reference 进入 terminal_hold
desired_speed 变成 0
```

这样任务就不再同时要求“停在终点”和“继续保持速度”。

然后从上一轮 line checkpoint 继续微调 2M steps，稍微加强位置误差和 progress 奖励。

结果：

```text
成功率: 100%
crash: 0%
平均横向误差: 约 0.077m
p90 横向误差: 约 0.194m
平均速度误差: 约 0.072m/s
动作变化: 很小
```

通俗讲：底层 tracker 现在能沿一条短直线走，并且不会明显偏线、不会速度误差过大。

下一关是 `heading_tracking`：

```text
让 tracker 在飞行或悬停时对准期望朝向
```
