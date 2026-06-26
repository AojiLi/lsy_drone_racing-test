# v56 Task 2：降低 cross 速度，但实际没变好

这一轮仍然没有训练 PPO，没有换 checkpoint，也没有改 `config/level3.toml`。

这轮只改一个东西：

```text
cross 阶段 desired_speed：0.52 m/s -> 0.32 m/s
```

## 结果

固定测试：

- seeds：`101-120`
- 每个 seed：`500 step`
- checkpoint：zigzag 合格 tracker
- 赛道：原始 `config/level3.toml`

结果：

```text
gate0 pass：2/20
first-gate progress：19/20
contact：20/20
fake recover：0
```

和 Task3 / Task4 基本一样，没有突破。

## 关键发现

虽然 planner 的目标速度变成了 `0.32 m/s`，但飞机实际在 gate-local X
方向上的速度没有明显降下来。

通俗说：

```text
planner 说慢一点，
但底层 tracker 实际没有慢下来多少。
```

所以单纯调 `desired_speed` 不是主瓶颈。

## 下一步

先不要继续盲调 planner 常数。

下一步应该补 trace 指标：

```text
aperture_y
aperture_z
aperture_yz_error
```

也就是每一步都记录“飞机到底离门洞中心多远”。现在很多判断只能用
gate-local Y/Z 近似，不够精确。

补完这个指标后，再跑同样的 20 个 seeds，看每个失败 seed 到底是：

```text
对准不够
实际速度太快
reference 点太激进
还是 tracker 跟不住
```
