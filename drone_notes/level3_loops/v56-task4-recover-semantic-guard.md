# v56 Task 4：修掉 planner 自己宣布 recover 的问题

这一轮仍然没有训练 PPO，没有换 checkpoint，没有改 `config/level3.toml`。

这轮只修一个语义问题：

```text
环境没有切 target_gate，planner 就不能进入 recover。
```

之前 seed 106 发生过这种情况：

```text
环境还在 target_gate 0
planner 却进入 phase 5 recover
并且持续了 500 step
```

这很危险，因为等于 planner 自己认为“过门了”，但比赛环境并没有承认。

## 修改

现在 `GeometricSlowGatePlanner` 不再根据 local X 直接进入 phase 5。

同一个 `target_gate` 下，最多只能到 cross：

```text
cruise -> slowdown -> align -> cross
```

只有环境真正切到下一个 `target_gate`，planner 才能重置到下一门的流程。

## 结果

固定测试：

- seeds：`101-120`
- 每个 seed：`500 step`
- checkpoint：zigzag 合格 tracker
- 赛道：原始 `config/level3.toml`

结果：

```text
fake recover：0
recover_before_gate_switch：0
gate0 pass：2/20
first-gate progress：19/20
contact：20/20
```

这说明：

```text
语义修对了，但性能还没变好。
```

以前 planner 会假装 recover，现在不会了；但不假装之后，很多 seed 变成了在
cross 或 near-plane 状态里撞掉。

## 下一步

下一步应该做 Task 3：

```text
near-plane backout
```

意思是：

```text
如果已经很接近门平面，
但 Y/Z 偏差太大，
不要硬穿，
退回 align，重新对准。
```

这个比直接降低 cross speed 更优先，因为现在的问题不是“正中间飞太快”，而是
“偏着还继续硬穿”。
