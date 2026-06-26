# v56 Task 3：加了 near-plane backout，但实际没触发

这一轮还是没有训练 PPO，没有换 checkpoint，也没有改 `config/level3.toml`。

这轮只加一个策略：

```text
如果飞机已经在门平面附近，
但 Y/Z 偏差大于 0.30m，
就不要继续 cross，
退回 align。
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

和上一轮 Task4 完全一样。

最关键的是：

```text
phase 4 -> phase 3 的 backout 次数 = 0
```

也就是说，这个规则虽然写进去了，但这组 seeds 里几乎没有真正触发。

## 结论

Task3 不是代码越界，而是对当前失败路径没有作用。

现在更像是：

```text
cross 阶段太激进 / 速度太快，
tracker 来不及修正，
然后在门附近撞掉。
```

所以下一步应该做 Task2：

```text
cross slowdown
```

也就是只把 cross 阶段期望速度从 `0.52 m/s` 降到大约 `0.32 m/s`。
