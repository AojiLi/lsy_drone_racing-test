# v62d 10 个候选总结

这次不是又开一个训练，而是按 loop 规则停下来复盘。

原因很简单：

```text
v62d_001 到 v62d_010
一共 10 个候选
没有一个真正超过当前基线 v62c 7M
```

所以现在不应该自动开 v62d_011。

## 当前最好是谁

当前最好还是：

```text
v62c 7M
```

checkpoint：

```text
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

它不是完美 tracker，但目前还没有候选能稳定超过它。

## 这 10 轮学到了什么

最重要的发现是：

```text
速度服从 和 空间精度 现在互相打架
```

通俗说：

```text
让 PPO 更听速度 -> 它容易偏离轨迹
让 PPO 更贴轨迹 -> 它又不听速度
```

这不是一个简单“再加一点 reward”就能解决的问题。

## 最有价值的候选

最有价值的是：

```text
v62d_008
```

它第一次明确让速度变好了：

```text
velocity error: 0.7397 -> 0.5708
```

但是它的问题也很明显：

```text
position error: 0.6573 -> 0.7943
```

也就是：速度听话了，但飞得不够贴轨迹。

## v62d_009 和 v62d_010 为什么没接住

v62d_009 想把空间拉回来：

```text
空间是拉回来了
速度突破没了
```

v62d_010 想在 v62d_008 上加 cross-track reward：

```text
5M: 轨迹更贴，但速度很差
30M: 速度回来一点，但轨迹又崩了
```

所以这两轮证明：

```text
粗暴的空间保护
不能同时保住 v62d_008 的速度突破
```

## 训练系统本身是不是坏了

目前看不是主要问题。

好的地方：

```text
tanh action path 正常
action clipping 基本为 0
logprob 一致性约 3e-7
W&B 正常
训练速度约 1.2M-1.3M env steps/s
```

但 critic 仍然弱：

```text
explained variance 接近 0
value 对不同状态分不太开
return 压力很大
```

这可能是后面要解决的问题，但之前单纯 value scaling 没有成功。

## 下一步

现在正确动作是：

```text
暂停 v62d 自动候选
等你 review 后再决定方向
```

我建议你在下面几个方向里选一个：

```text
1. command-conditioned reward
   不再全局加 cross-track，而是按 pass / hold / slow / recover 分开设计。

2. 更认真解决 critic/value
   不是简单 value_target_scale，而是更系统地让 critic 学起来。

3. staged command curriculum
   先分别练 pass、brake、slow-through、recover，再混合。

4. 改网络/记忆结构
   如果你认为当前 MLP tracker 对 command 切换能力不足。

5. 暂停 v62d，回到 planner integration 或其他路线。
```

一句话：

```text
v62d 已经证明“速度能学会”，但还没有找到“速度和轨迹精度同时保住”的方法。
现在需要你做一次方向选择，而不是继续自动乱试第 11 个候选。
```
