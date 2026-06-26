# v57a：把 cross 入口 reference 从“突然跳点”改成“连续推进”

这一轮没有训练 PPO，也没有换 checkpoint、改 reward、改 observation、加
MPPI，`config/level3.toml` 没变。

固定测试还是：

```text
checkpoint：v55 zigzag 合格 tracker
seeds：101-120
每个 seed：500 steps
赛道：config/level3.toml
```

## 这轮改了什么

上一轮 v57 发现，planner 从 align 进入 cross 的那一下，reference 会突然
跳大约：

```text
0.74m
```

这会让 tracker 突然追一个很远的点，动作也跟着跳。

v57a 做的事情很窄：

```text
phase3 -> phase4 时，
reference 第一步最多只往前移动 0.28m，
后面再滚动靠近 aperture / post-gate。
```

通俗说：

```text
先把路线别画成突然急拐。
```

## 结果

这个修复本身是成功的：

```text
phase3 -> phase4 reference jump：0.740m -> 0.280m
phase3 -> phase4 reference error：0.783m -> 0.340m
phase3 -> phase4 action delta：0.727 -> 0.491
```

也就是说，planner 给 tracker 的路线确实变平滑了。

但是 Level3 gate 结果没有变好：

```text
gate0 pass：2/20
first-gate progress：19/20
contact：20/20
early termination：2/20
all finite：true
```

速度问题也基本没变：

```text
phase4 目标速度：0.32m/s
near-plane 实际 gate-local X 速度中位数：约 0.52m/s
p75：约 0.69m/s
```

## 这说明什么

这轮把 planner 的明显问题修掉了：路线不再突然跳。

但无人机还是在门附近偏快，还是 contact。现在更像是底层 tracker 的能力
不够：

```text
planner 已经更温柔地说“慢慢穿过去”
但 tracker 实际还是刹不住、跟不细、速度压不下来
```

## 下一步

我不建议继续普通几何 planner 小调。

下一步更合理的是：

```text
v58_tracker_planner_like_reference_training
```

也就是专门训练一个更会跟 planner reference 的底层 PPO tracker。

它不是学“直接跑 Level3”，而是学：

```text
给一串 reference points / reference velocity / desired heading，
它能稳、准、慢下来、不过冲地跟过去。
```

重点练：

```text
慢速跟点
到点刹车
短直线 / L 形 / 小弯曲轨迹
pre-gate -> aperture -> post-gate 这种小轨迹
把速度从 0.7m/s 降到 0.25-0.35m/s
低 overshoot
heading 稳定
```

一句话：

```text
v57a 证明路线已经不再乱跳；
接下来要训练一个真的会稳稳跟路线的底层 tracker。
```
