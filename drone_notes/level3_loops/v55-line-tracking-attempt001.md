# v55 line_tracking attempt001 做了什么

这一轮没有通过第五关 `line_tracking`。

结果不是飞机不会飞，也不是会 crash：

```text
success: 100%
crash: 0%
平均横向误差: 约 0.072m，合格
p90 横向误差: 约 0.229m，略高于 0.22m 门槛
平均速度误差: 约 0.311m/s，明显高于 0.18m/s 门槛
动作变化: 很小，合格
```

通俗讲：它能沿着线走，但走得太慢。

更关键的是，我发现这个任务本身有个语义矛盾：

```text
line_tracking 的线长约 0.9m
期望速度是 0.38m/s
大约 2.4 秒就走到终点
但 evaluator 会评估 10 秒
```

旧逻辑里，reference 位置到终点后停住了，但 desired speed 还不是 0。
这等于同时要求：

```text
停在终点
继续保持速度
```

这会把速度误差算得很难看。

下一步不是盲目再训 5M，而是先修这个 terminal hold 语义：

```text
轨迹走到终点后，desired_speed 改成 0
把后半段变成“终点保持”
```

修完后，重新评估当前 checkpoint。如果修完就过关，说明这个 checkpoint 本来就已经学会了合理的线跟踪；如果还不过，再专门加强速度跟踪训练。
