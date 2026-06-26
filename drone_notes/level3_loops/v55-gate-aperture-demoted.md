# v55 gate-aperture 降级说明

这次改动的核心是：不再把 `gate_aperture_reference` 当成底层 PPO tracker 必须通过的第 11 关。

原因很直观：我们现在的架构不是让 PPO 自己决定怎么过门，而是：

```text
上层 planner 负责决定接下来走哪串 reference points
底层 PPO tracker 负责稳定、精准、平滑地跟踪这串 reference
```

所以底层 PPO 最重要的能力不是“理解门”，而是“给它一串点，它能跟住”。之前 gate-aperture attempt001 学到的是：能在门前附近稳定、不撞、Y/Z 对得比较准，但它不愿意真正穿过门平面。这说明继续给它加 gate reward，可能会把问题带回“让底层 PPO 学过门语义”，和我们现在的分工不一致。

现在 loop 已经改成：

- 前 10 个 free-space tracker 阶段已经通过，最后一个是 `zigzag_or_lemniscate_tracking`。
- `gate_aperture_reference` 变成可选诊断，不再挡住主线。
- 下一步直接进入 `planner_integration_smoke`。
- planner smoke 会在不改 `config/level3.toml` 的前提下，把上层 planner 接到底层 tracker 上，看它能不能至少产生 first-gate progress 和 gate-0 pass。

如果 planner smoke 失败，下一步不是立刻继续训 gate-aperture，而是先判断：

- planner 生成的 reference 点是不是设计得不好；
- tracker 是不是对某类 planner 轨迹跟不住；
- 还是 observation / action / reference 包装有 bug。

一句话：这次不是放弃过门，而是把“过门”放回 planner 的责任里，把 PPO tracker 的目标收窄到真正该学的东西：跟轨迹。
