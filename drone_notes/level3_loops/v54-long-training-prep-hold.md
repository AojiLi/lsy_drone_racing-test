# v54 长训准备：这次不应该开长训

这轮的目的不是直接长训，而是先判断：

```text
现在这个 v54 PPO tracker 值不值得开一晚上的长训练？
```

结论很明确：**暂时不值得。**

原因很简单：

```text
它会动，也会朝第一个门方向动；
但还不会稳定穿过第一个门。
```

这次做了两段 bounded diagnostic training：

1. 从之前的 v54 checkpoint 继续练 `gate_aperture`，32k steps。
2. 再用更稳的设置练 `level3` tracker，32k steps：
   - roll/pitch 上限从 50deg 降到 35deg；
   - 加强动作平滑；
   - 加强 gate center；
   - 加强 crash penalty。

两个 W&B run：

- `v54_tracker_longprep_gate_aperture_lr1e4_32k_20260625`
- `v54_tracker_longprep_level3_stability_rp35_32k_20260625`

最后用 unchanged `config/level3.toml` 跑 seeds `101-120`。

结果：

```text
动作 finite：通过
checkpoint 加载：通过
多数 seed 有 first-gate progress：通过
至少一个 seed 过 gate 0：失败
早停改善：失败
```

最好的诊断 checkpoint 是：

`lsy_drone_racing/control/checkpoints/v54_reference_tracker_longprep/v54_tracker_gate_aperture_lr1e4_32k.ckpt`

但它也只是：

```text
14 / 20 个 seeds 有向第一个门前进
0 / 20 个 seeds 真正过 gate 0
18 / 20 个 seeds 在 50 步前早停
```

所以这不是“差一点，开长训就会好”的状态。

现在的问题更像是：

```text
底层 tracker 还没有学会 gate-aperture crossing 这个小技能。
```

下一步应该先做一个更专门的 gate-aperture completion curriculum：

- 让训练从门前、对准、穿门、门后恢复这些阶段开始；
- 明确奖励安全穿过 gate plane；
- 先要求 mini-task 里能过门；
- 再回到 Level3 seeds 101-120 做 smoke；
- 只有至少一个 seed 能过 gate 0，才考虑开 10M/30M 长训。

所以目前没有给长训练命令，这是故意的。现在硬开长训，比较像是在花时间放大一个还没学会的底层技能。
