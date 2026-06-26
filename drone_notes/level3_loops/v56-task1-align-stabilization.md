# v56 Task 1：门前对准变严格，但还没解决问题

这一轮没有训练 PPO，也没有换 checkpoint，更没有改 `config/level3.toml`。

这轮只做了一件事：

```text
让 planner 不要太早进入 cross 穿门阶段。
```

之前的问题是，飞机只要接近门平面，哪怕 Y/Z 还没对准，也可能进入
cross。现在改成：

```text
Y/Z 误差 <= 0.22m
并且 gate-local X 方向速度 <= 0.85m/s
才允许从 align 进入 cross
```

同时 trace 里新增了 `gate_local_vx`，以后能看飞机靠近门时沿门轴方向的速度。

## 结果

固定测试：

- seeds：`101-120`
- 每个 seed：`500 step`
- checkpoint：zigzag 合格的 tracker checkpoint
- 赛道：原始 `config/level3.toml`

结果：

```text
gate0 pass：2/20
first-gate progress：19/20
contact：19/20
early termination：2/20
all finite：true
```

对比上一版 baseline：

```text
baseline gate0 pass：3/20
baseline first-gate progress：20/20
baseline contact：15/20
```

所以这轮没有变好，反而更保守、更容易撞。

## 最关键的新发现

这轮暴露出一个更重要的问题：

```text
planner 仍然会在环境没有真正判定过门时，自己进入 recover 阶段。
```

具体是 seed 106：

```text
phase_id = 5，也就是 recover
但 pre_target_gate == post_target_gate == 0
max_gate_index 也还是 0
持续了 500 step
```

通俗说：环境还没说“你过门了”，planner 自己已经按“过门后恢复”来飞。
这违反了 v56 的核心规则：

```text
只有环境 target_gate 真的变化，才算真实过门。
同一个 target_gate 下禁止 recover。
```

## 下一步

下一轮不应该先调 cross speed。应该先修这个语义漏洞：

```text
recover_after_environment_target_gate_switch_semantic_guard
```

目标是：

```text
recover_before_gate_switch_count = 0
fake_recover_count = 0
```

也就是 planner 不能再自己宣布过门。先把这个判定权还给环境，再继续调
cross 慢速、偏离回退等策略。
