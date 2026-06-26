# v60 brake ramp generator

这轮补的是一个很关键的小洞：

```text
不能让 PPO 看到“上一秒还在飞，下一秒突然停车”。
```

之前 v60 已经变成了连续小轨迹，但 pass 到 hold 的速度变化仍然可能太突然。
这会让底层 tracker 学成：

```text
先冲过去，然后硬刹
```

现在改成：

```text
飞 -> 提前减速 -> 停住
```

具体来说，pass-through 前段还是巡航，大约 `0.55-0.78m/s`；接近刹车点时，
速度会平滑降到 `0.15-0.24m/s`；之后才进入真正的 hold/brake，目标点基本
不动，期望速度为 0。

这更像真实 planner 会给底层控制器的命令：

```text
先往目标点飞
提前慢下来
停稳/对准
再低速穿越
最后恢复速度
```

这轮没有改 `config/level3.toml`，没有改 observation 维度，没有加 gate reward。
它还是干净的 v60 底层 tracker。

检查结果：

```text
ruff passed
pytest 42 passed
1024-step trainer smoke passed on CPU
checkpoint-backed evaluator smoke passed plumbing
stage gate 未通过是预期，因为 1024 steps 不是学习训练
```

下一步可以正式跑 v60 8M maturation。
