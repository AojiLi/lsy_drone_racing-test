# Loop 121: structural_hidden512_v50_update_pressure_conversion_30m

- 生成时间: 2026-06-24T21:39:38+00:00
- Trial: `level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m`
- 训练赛道: `level3.toml`
- 硬评估赛道: `level3.toml`
- Observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- 结构假设: `v50_hidden512_update_pressure_conversion_from_loop110_3m`

## 一句话

这轮没有达到 60% 完赛率目标；它提供的是下一步该怎么改的证据。

## 这轮到底做了什么

- 名字: `structural_hidden512_v50_update_pressure_conversion_30m`
- 训练步数: `30000000`
- 初始 checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt`
- 网络/训练结构: `mlp_2x_tanh`
- hidden_dim: `512`
- W&B run: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m`

## 结果怎么读

- 最好 checkpoint: `level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m:25M`
- checkpoint 文件: `lsy_drone_racing/control/checkpoints/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_step_025000000.ckpt`
- 完赛率: **18.0%**
- 平均过门数: **1.56**
- 撞毁率: **80.0%**
- timeout: **2.0%**
- 成功时平均用时: **6.283s**
- 是否达到目标: **否**

## 和当前最好结果相比

- 当前全局最好: level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight:1M: success 21.0%, mean gates 1.66, crash 79.0%, time 7.578s

## 通俗理解

- W&B 曲线和训练 reward 只是诊断，真正算数的是 hard eval。
- 如果完赛率没有涨，但成功时速度够快，说明主要问题通常不是速度，而是稳定过门、避障和连续控制。
- 如果 final checkpoint 比中间 checkpoint 差，后续要优先选中间最好点，不默认 final 最好。

## 下一步

- 下一条 lane: `v51_planner_guidance_obs_ppo256_from_loop110_3m`

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py --max-iterations 1 --wandb-enabled --wandb-entity aojili77-technical-university-of-munich --structural-hypothesis v51_planner_guidance_obs_ppo256_from_loop110_3m --codex-autonomous-loop --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_analysis.md --research-packet experiments/level3_ppo_loop/research/2026-06-24_level3_v51_planner_guidance_obs_ppo256_plan.md --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-24_loop121_reject_v50_launch_v51_planner_guidance_obs_ppo256.md
```

## 重要文件

- analysis: `experiments/level3_ppo_loop/analysis/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_analysis.md`
- subagent_reviews: `experiments/level3_ppo_loop/analysis/level3_loop_121_structural_hidden512_v50_update_pressure_conversion_30m_subagent_reviews.md`
- decision: `experiments/level3_ppo_loop/decisions/2026-06-24_loop121_reject_v50_launch_v51_planner_guidance_obs_ppo256.md`

## Reader-Note 子 Agent 补充

# Level3 loop121 读者笔记

最新完成的是 loop121，也就是 v50：从 loop110/v39 的 3M checkpoint 继续，尝试更大的 512 隐层网络，并加强 PPO 的“更新力度”。PPO 可以理解成训练策略网络的算法；这轮主要想让策略真的学动，而不是训练曲线看起来停住。

结果：v50 确实修好了上一轮 v49 那种“几乎不更新”的问题，但没有解决 Level3。最好 checkpoint 是 25M：成功率 18%，平均过门数 1.56，撞毁率 80%，成功时平均 6.283 秒。最终 checkpoint 还掉到 15% 成功率、1.45 平均过门数。目标是成功率至少 60%，且成功时平均不超过 7 秒，所以远没达标。当前全局最好仍是 loop107/v37 1M：21% 成功率，1.66 平均过门数，79% 撞毁率，7.578 秒。

没解决的核心原因：成功的飞行已经够快，问题不是速度，而是大多数种子还飞不稳、过不了足够多的门，撞毁太多。v50 让训练更新更健康，但这些更新只带来小幅评测提升，没有真正学会更可靠的路线意图、门洞/通道选择和避障判断。

下一轮 v51 会试 planner-guidance observation。意思是：加入一个确定性的“路线提示”模块，把局部目标方向、门框坐标、避障方向、最近障碍距离、期望速度等 13 个数字追加到观测里，让 PPO 策略看见更清楚的局部路线信息。

技术上会改变：观测布局换成 `level3_planner_guidance_2obs_local_history_v12`，planner 版本是 `local_gate_waypoint_obstacle_risk_v1`，策略网络回到 2x256 Tanh PPO Actor，从 loop110/v39 3M warm-start，并对新增 planner 输入通道做零填充初始化。

不会改变：`config/level3.toml` 赛道、门、障碍、随机化和硬评测不变；planner 不输出动作、不接管控制、不做安全盾、不做 MPC、不回放固定种子路线。动作仍然只由 PPO Actor 输出 roll/pitch/yaw/thrust。

下一轮重点看：成功率是否到 25% 以上，平均过门数是否到 1.75 以上，撞毁率是否降到 75% 以下；同时看是否出现新的成功种子。训练诊断上看 `approx_kl`、`clipfrac`、熵/action std、value loss、explained variance，以及 passed gate、finished、crashed、gate stage。v51 如果所有里程碑都低于 16% 成功率或 1.50 平均过门数，就应暂停做 planner 特征诊断。
