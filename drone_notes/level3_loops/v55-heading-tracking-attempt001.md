# v55 heading_tracking attempt001 做了什么

这一轮通过了第六关：`heading_tracking`。

通俗讲，这一关不是让飞机过门，而是测试：

```text
给 PPO 一个期望朝向
它能不能稳定地把机头/航向对过去
同时动作不要乱抖、不要 crash
```

训练方式：

```text
从 line_tracking 通过的 checkpoint 继续
1024 个并行环境
总共 4M steps
每 1M 保存一个 checkpoint
```

结果最好的不是最终 checkpoint，而是中间的 2M checkpoint：

```text
成功率: 100%
crash: 0%
平均 heading error: 约 0.148 rad
p90 heading error: 约 0.153 rad
平均 yaw rate: 0
动作变化: 很小
```

final checkpoint 也能过，但 heading error 已经更接近上限，所以选 2M 作为更稳的通过点。

这说明底层 tracker 现在不只是会走直线，也能按 reference 要求保持/对齐朝向。

下一关是 `multi_point_reference`：

```text
给它多个 reference points
看它能不能平滑切换、不要冲过头、不要动作乱跳
```
