# v55 curve_tracking attempt001 做了什么

这一轮通过了第九关：`curve_tracking`。

这一关的意思是：

```text
让 PPO 跟一条平滑弯曲轨迹
不是直线，也不是简单 L 形折线
```

为什么重要：

```text
planner 之后给出的安全轨迹很可能是弯的
底层 PPO 必须能平滑跟弯
不能大幅振荡
```

训练方式：

```text
从 L-shape 通过的 checkpoint 继续
1024 个并行环境
总共 10M steps
每 1M 保存一个 checkpoint
```

这轮很顺，所有 checkpoint 都过了 gate。最终选 9M checkpoint：

```text
path completion: 100%
crash: 0%
平均横向误差: 约 0.093m
p90 横向误差: 约 0.204m
振荡分数: 约 0.011
动作变化: 很小
```

final checkpoint 的平均误差更低，但振荡和动作变化更大，所以选 9M 作为更稳的下一关起点。

下一关是 `zigzag_or_lemniscate_tracking`：

```text
更急的转弯 / zigzag / 类 8 字轨迹
```
