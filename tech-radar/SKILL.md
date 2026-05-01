---
name: tech-radar
description: |
  AI技术雷达 — 搜索最新AI模型研究成果与排行榜。

  TRIGGER when: 用户要求搜索最新AI技术动态、模型排行榜、
  研究论文发布、世界模型/VLA/VLN进展、LLM/STT/TTS/S2S发布状态。
  也适用于 "帮我查一下最新的AI模型"、"最近有什么新的大模型"、
  "AI领域有什么新进展"、"推送技术雷达"、"发送今日报告" 等查询。
  每天 09:30 由 OpenClaw cron 自动触发 daily-push。
---

# 技能：AI技术雷达

## 触发条件

用户要求搜索/了解：
- 最新AI模型研究成果（世界模型、VLA、VLN、机器人、自动驾驶）
- 大模型发布状态和排行榜（LLM、STT、TTS、S2S）
- AI领域最新进展和趋势

## 子命令分发

从 `$ARGUMENTS` 解析子命令，或从自然语言推断：

| 子命令 | 说明 | 子文档 |
|--------|------|--------|
| `research` | 最新AI研究成果（🤖机器人：VLA/VLN/模仿学习/RL/世界模型/LLM-Planner/3D/触觉/多机/人形；🚗自动驾驶：E2E/世界模型/BEV/占据/VLM/轨迹/LiDAR/3D重建/地图/仿真；🌐通用：世界模型/3D基础/视觉基础/扩散/多模态LLM） | `research.md` |
| `leaderboard` | 模型排行榜（LLM/STT/TTS/S2S） | `leaderboard.md` |
| `releases` | 最新模型发布动态 | `releases.md` |
| `all` | 全面扫描（默认） | 依次执行以上三项 |
| `daily-push` | 每日定时推送（更新文档 + 推送到飞书群聊） | `daily-push.md` |

未指定子命令时，根据用户意图推断；若无法推断，默认执行 `all`。

## 研究查询方式

用户可能按**领域**、**范式**或**会议**发起查询，三种方式都应支持：

- **按领域**："自动驾驶最新研究"、"机器人领域有什么突破" → 搜索该领域下所有范式
- **按范式**："VLA最新进展"、"世界模型有什么新论文" → 搜索所有领域下该范式
- **按会议**："CVPR 2026 有什么机器人论文" → 在指定会议范围内搜索所有领域和范式
- **交叉查询**："自动驾驶的世界模型" → 搜索该领域下该范式

## 输出格式

每次搜索结果以结构化报告呈现：

```
## 📡 AI技术雷达 — {日期}

### 🔬 研究前沿
{research.md 的输出}

### 🏆 模型排行榜
{leaderboard.md 的输出}

### 🚀 最新发布
{releases.md 的输出}

---
数据来源：{列出所有引用的URL}
```

## 飞书文档 ID

| 文档 | document_id | 链接 |
|------|-------------|------|
| 排行榜 | `Sjfidl7rxolTHkxsplKctiWDngf` | https://www.feishu.cn/docx/Sjfidl7rxolTHkxsplKctiWDngf |
| 模型动态 | `ZPGYdeGMeosecwxd2IFcs3AUnnh` | https://www.feishu.cn/docx/ZPGYdeGMeosecwxd2IFcs3AUnnh |

## 飞书群聊 ID（daily-push 推送目标）

| 群聊名称 | chat_id |
|----------|---------|
| 工程研发 | `oc_895cca9ec34debe07923788a1aa711cb` |
| True Embodiment | `oc_ab35190d8e31c69f4b1aa821c374a206` |
| 智能体研发范式共创 | `oc_67be5ebb27fc465a4bfa0191219ca8a0` |

## 每日定时推送 (daily-push)

- **触发时间**：每天 09:30（OpenClaw cron 任务）
- **推送内容**：三段消息（排行榜速报 / 模型发布动态 / 研究前沿），每段含摘要 + 文档链接
- **更新策略**：增量更新，不重复已有内容
- **详细流程**：见 `daily-push.md`

## 通用规则

- 使用 `WebSearch` 工具进行搜索，使用 `WebFetch` 获取页面详情
- 搜索时使用英文关键词以获取更全面的结果
- 报告以中文呈现，但保留英文术语和论文标题
- 每个搜索结果必须附带来源链接
- 关注 **2025-2026** 的最新信息
- 对于论文，优先关注顶会（NeurIPS, ICML, ICLR, CVPR, ICRA, CoRL, IROS, RSS, AAAI, ITSC, IV）和顶级期刊（Nature, Science, Science Robotics, Nature Machine Intelligence, T-RO, T-ITS, T-PAMI, RA-L, IJRR）
- 搜索结果应涵盖中国和国际两个视角
