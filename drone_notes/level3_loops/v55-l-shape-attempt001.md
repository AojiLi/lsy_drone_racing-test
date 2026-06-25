# v55 l_shape_tracking attempt001 做了什么

这一轮通过了第八关：`l_shape_tracking`。

这一关的意思是：

```text
让 PPO 跟一个 L 形路线
也就是先直走，再转一个弯
```

为什么重要：

```text
真实 planner 不会只给直线
它会经常给“先到这里，再转过去”的局部路线
所以底层 PPO 必须能处理拐角
```

训练方式：

```text
从 multi_point_reference 通过的 checkpoint 继续
1024 个并行环境
总共 8M steps
每 1M 保存一个 checkpoint
```

最好的通过点是 5M checkpoint：

```text
corner completion: 100%
crash: 0%
平均横向误差: 约 0.119m
p90 横向误差: 约 0.203m
拐角 overshoot: 约 0.097m
动作变化: 很小
```

final checkpoint 虽然平均误差更低，但动作变化明显变大，所以不选 final 作为下一关起点。

通俗讲：底层 tracker 已经能处理一个简单拐角。下一关是 `curve_tracking`，也就是让它跟更平滑的弯曲轨迹。
