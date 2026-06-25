# Loop 122: structural_v51_planner_guidance_obs_ppo256_30m

- 生成时间: 2026-06-25T00:36:53+00:00
- Trial: `level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m`
- 训练赛道: `level3.toml`
- 硬评估赛道: `level3.toml`
- Observation: `level3_planner_guidance_2obs_local_history_v12`
- 结构假设: `v51_planner_guidance_obs_ppo256_from_loop110_3m`

## 一句话

这轮没有达到 60% 完赛率目标；它提供的是下一步该怎么改的证据。

## 这轮到底做了什么

- 名字: `structural_v51_planner_guidance_obs_ppo256_30m`
- 训练步数: `30000000`
- 初始 checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt`
- 网络/训练结构: `mlp_2x_tanh`
- hidden_dim: `256`
- W&B run: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m`

## 结果怎么读

- 最好 checkpoint: `level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m:10M`
- checkpoint 文件: `lsy_drone_racing/control/checkpoints/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_step_010000000.ckpt`
- 完赛率: **18.0%**
- 平均过门数: **1.42**
- 撞毁率: **81.0%**
- timeout: **1.0%**
- 成功时平均用时: **6.991s**
- 是否达到目标: **否**

## 和当前最好结果相比

- 当前全局最好: level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight:1M: success 21.0%, mean gates 1.66, crash 79.0%, time 7.578s

## 通俗理解

- W&B 曲线和训练 reward 只是诊断，真正算数的是 hard eval。
- 如果完赛率没有涨，但成功时速度够快，说明主要问题通常不是速度，而是稳定过门、避障和连续控制。
- 如果 final checkpoint 比中间 checkpoint 差，后续要优先选中间最好点，不默认 final 最好。

## 下一步

- 下一步不是训练，而是 `hold_for_v51_planner_diagnostics`。
- 暂时没有下一条训练命令；不要继续 v51 as-is，也不要直接跑 analyzer 给出的 reward-number 命令。
- 先做 planner-feature 诊断：确认 checkpoint metadata、train/eval observation parity、planner 特征尺度/裁剪、成功/失败 seed 变化，以及 planner-channel input weights 是否真的学起来。

如果诊断发现 metadata、parity、scaling 或 feature bug，再走 builder/checker gate 做最小修复；如果诊断干净，再写新的 v52 structural packet。

## 重要文件

- analysis: `experiments/level3_ppo_loop/analysis/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_analysis.md`
- subagent_reviews: `experiments/level3_ppo_loop/analysis/level3_loop_122_structural_v51_planner_guidance_obs_ppo256_30m_subagent_reviews.md`
- decision: `experiments/level3_ppo_loop/decisions/2026-06-25_loop122_hold_for_v51_planner_diagnostics.md`

## Reader-Note 子 Agent 补充

loop122 测的是 v51：在原来的 v5 观测里，额外加入一组 planner guidance 特征。通俗说，就是让 PPO 多看到一些“局部路线意图”的提示，例如往哪个门走、附近障碍风险怎样。但要特别注意：planner 只是提供 observation，不是动作控制器；真正输出 roll/pitch/yaw/thrust 的仍然只有 PPO Actor。

这一轮仍然在未改变的 config/level3.toml 上做 hard eval。Level3 赛道、门、障碍、随机化和验证种子都没有被放松，所以结果可以和之前的全局 best 公平比较。

loop122 最好的 checkpoint 是 10M：成功率 18%，平均过门数 1.42，撞毁率 81%，成功样本平均时间 6.991s。时间已经接近目标的 7 秒以内，但成功率远低于目标 60%，而且平均过门数不够高。

20M checkpoint 的平均过门数更高，达到 1.57，但成功率只有 16%，撞毁率 84%，成功时间 7.013s。也就是说，它看起来能多推进一点门，但没有把这种推进稳定转化成更多完赛。

final checkpoint 更差，掉到 12% success、1.42 mean gates、88% crash。整条曲线是早期有一点峰值，后面没有继续变强，说明不能简单继续拉长训练到 60M 或 90M。

和当前全局 best 比，loop122 没有突破。全局 best 仍然是 loop107 的 1M checkpoint：21% success、1.66 mean gates、79% crash、7.578s mean successful time。loop122 的成功时间更快一些，但成功率、过门数和撞毁率都落后。

三个 review 的共同判断是：PPO 本身不是明显“没学动”。W&B 里 KL、clipfrac、entropy、explained variance 等指标都还算活跃，训练 reward 也在涨；问题是这些训练信号没有转成 hard eval 上的稳定过门和完赛。

所以 main-agent 决策是暂停：hold_for_more_analysis。不要继续 v51 as-is，也不要直接按 analyzer 的 reward-number 建议开下一轮。现在更像是 planner 特征本身的语义、尺度、训练/评估一致性，或者 policy 是否真的使用了这些新输入，出了问题。

下一步要诊断的是：checkpoint metadata 是否确实启用了 planner guidance；train/eval 的 planner observation slice 是否一致；planner 特征在验证种子上的分布是否过大、过小、饱和或被裁剪；v51 到底赢了哪些 seed、丢了哪些旧 frontier seed；以及新加的 planner input weights 是否真的从零开始学出了有意义的权重。

一句话总结：v51 是一次合理的“给 PPO 更多路线提示”的结构尝试，但目前提示没有转化成更稳定的 Level3 完赛。暂停不是因为目标达成，而是因为继续训练前必须先弄清楚这些 planner observation 有没有被正确传入、尺度是否合适、以及 PPO 是否真的在用它们。
