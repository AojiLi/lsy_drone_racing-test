# v57：planner reference / tracker interface 审计小结

这轮没有训练 PPO，也没有换 checkpoint、改 reward、改 observation、加
MPPI，`config/level3.toml` 没变。

固定测试还是：

```text
checkpoint：v55 zigzag 合格 tracker
seeds：101-120
每个 seed：500 steps
赛道：config/level3.toml
```

结果：

```text
gate0 pass：2/20
first-gate progress：19/20
contact：20/20
all finite：true
```

## 这轮主要看什么

这轮不是看“有没有过关”，而是看失败到底更像：

```text
A. planner 给的 reference 有问题
B. tracker 跟不住 / 刹不住
C. 两者都有
```

## 关键发现

最重要的数字是：

```text
phase3 -> phase4 reference jump：0.74m
phase3 -> phase4 reference error：约 0.78m
phase3 -> phase4 action delta：约 0.73
```

通俗说：

```text
进入 cross 的那一下，planner 给 tracker 的目标点突然跳了 0.74m。
tracker 当时离新目标点差不多 0.78m。
动作也在这一刻明显跳变。
```

所以现在不能简单说“tracker 太差，需要马上重训”。因为 planner 给它的
小路本身还不够温柔、不够连续。

同时，tracker 也确实有问题：

```text
planner 希望 phase4 速度是 0.32m/s
但实际 gate-local X 速度中位数约 0.52m/s
p75 约 0.70m/s
```

也就是：

```text
上层说慢一点
底层还是经常偏快
```

## 结论

这不是单纯 A，也不是单纯 B，而是：

```text
C. 两者都有
```

但应该先修 planner-interface。

原因很简单：如果 planner 进入 cross 时目标点突然跳 `0.74m`，那 tracker
跟不好是可以理解的。应该先把这条 reference 变成 tracker 更容易跟的小路，
再判断是否真的需要重训 tracker。

## 下一步建议

先做一个 planner-interface fix：

```text
v57a_cross_entry_reference_continuity_clamp
```

意思是：

```text
phase3 -> phase4 时，不要让 reference 一下跳 0.74m。
先从上一个 reference 附近开始，
再逐步滚动到 aperture / post-gate。
```

如果这个修完后，reference 已经平滑了，但 tracker 还是刹不住、速度还高、
还是 contact，那时再正式开启：

```text
v58_tracker_planner_like_reference_training
```
