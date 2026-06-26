# v62 Brax PPO Smoke 通俗记录

这次做的事情很明确：把之前“只会高速 rollout 的 JAX/Brax 探针”，接成了一个最小 PPO 训练闭环。

也就是说，现在不只是能让 1024 个环境在 GPU 上快速跑，还能完成：

```text
JAX policy
JAX rollout
GAE
PPO update
checkpoint
W&B offline log
短评估
```

最重要的结论：

```text
这个方向能训练，而且速度很快。
```

正式 smoke 跑的是：

```text
1024 envs x 32 steps
262144 total timesteps
8 个 PPO update
```

前两轮主要在编译，所以很慢。第 3 轮之后速度稳定在大约：

```text
1.09M - 1.33M env steps/s
```

之前 PyTorch fast path 大概是：

```text
39.8k env steps/s
```

所以排除编译后，JAX/Brax/Optax 这条路大约快：

```text
32 倍
```

训练没有崩：

```text
all_finite = 1.0
eval done_mean = 0.0
checkpoint 可以正常读取
W&B offline run 正常生成
```

但这个还不是“最终训练器”，也不是证明 tracker 已经学会了。它目前证明的是：

```text
纯 JAX PPO 训练管线是可行的，值得升级成正式 v60 tracker 训练后端。
```

下一步更合理的是：

```text
把这个 smoke 脚本工程化成正式 v62 trainer lane，
加 milestone checkpoint / resume / stage eval，
然后先跑 1M 左右，看 learning signal 是否真的变好。
```

这次没有改 `config/level3.toml`，也没有加入 gate reward。底层 tracker 仍然保持 v60 的干净目标：

```text
只学 generic reference command tracking，
不学过门，不学比赛进度，不学 finish reward。
```
