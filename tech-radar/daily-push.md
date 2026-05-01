# 子命令：daily-push — 每日技术雷达推送

## 触发条件

- 每天 09:30 自动触发（OpenClaw cron 任务）
- 手动触发：`/tech-radar daily-push`

## 推送目标群聊

| 群聊名称 | chat_id |
|----------|---------|
| 工程研发 | `oc_895cca9ec34debe07923788a1aa711cb` |
| True Embodiment | `oc_ab35190d8e31c69f4b1aa821c374a206` |
| 智能体研发范式共创 | `oc_67be5ebb27fc465a4bfa0191219ca8a0` |

### 如何查找群聊 chat_id

使用 `lark-cli im +chat-search` 命令，通过群名关键词搜索：

```bash
# 搜索群聊（用户权限）
lark-cli im +chat-search --as user --query "群名关键词"

# 示例
lark-cli im +chat-search --as user --query "工程研发"
lark-cli im +chat-search --as user --query "True Embodiment"
lark-cli im +chat-search --as user --query "智能体研发范式共创"
```

返回结果中的 `chat_id` 字段即为群聊 ID（格式：`oc_xxxxx`）。

> ⚠️ 注意：必须使用 `--as user`（用户权限），不支持 bot 权限。

## lark-cli 命令参考

### 更新飞书文档

```bash
# 覆盖更新文档（使用本地 markdown 文件）
lark-cli docs +update --as user --doc "文档ID" --mode overwrite --markdown "$(cat 文件路径.md)"

# 追加内容到文档
lark-cli docs +update --as user --doc "文档ID" --mode append --markdown "$(cat 文件路径.md)"

# 本技能使用的文档 ID
# 排行榜：Sjfidl7rxolTHkxsplKctiWDngf
# 模型动态：ZPGYdeGMeosecwxd2IFcs3AUnnh
```

### 发送消息到群聊

```bash
# 发送文本消息（bot 权限）
lark-cli im +messages-send --chat-id "oc_xxxxx" --text "消息内容"

# 发送 Markdown 消息（bot 权限）
lark-cli im +messages-send --chat-id "oc_xxxxx" --markdown "**加粗** 普通文本"
```

### 搜索群聊

```bash
# 按关键词搜索群聊（用户权限）
lark-cli im +chat-search --as user --query "关键词"
```

## 推送流程

### 第一步：检查文档更新

1. 读取飞书文档当前内容：
   - 排行榜文档：`Sjfidl7rxolTHkxsplKctiWDngf`
   - 模型动态文档：`ZPGYdeGMeosecwxd2IFcs3AUnnh`
2. 执行 `leaderboard` 和 `releases` 子命令，获取最新数据
3. 对比新旧内容，只更新有变化的部分（不重复写入已有的条目）

### 第二步：更新文档

**排行榜更新策略（增量）：**
- 如果 Elo 排名有变化，更新对应行
- 如果有新模型上榜，追加到表格
- 如果有模型掉出 Top 30，移除对应行
- 更新日期标题

**模型动态更新策略（增量）：**
- 如果有新的模型发布，追加到对应分类下
- 已有的条目不重复添加
- 更新日期标题
- 追加新的热门论文

### 第三步：生成三段推送消息

分别生成三段独立消息，每段包含摘要 + 文档链接：

**消息 1：排行榜速报**
```
📡 AI 技术雷达 — 排行榜速报 ({日期})

{摘要：当日排名变化亮点，如新上榜模型、排名大幅变动、国内厂商表现}

📊 完整排行榜：{飞书文档链接}
```

**消息 2：模型发布动态**
```
🚀 AI 技术雷达 — 模型发布动态 ({日期})

{摘要：当日新增的模型发布/更新，按重要性排序}

📄 完整动态：{飞书文档链接}
```

**消息 3：研究前沿**
```
🔬 AI 技术雷达 — 研究前沿 ({日期})

{摘要：当日新增的热门论文/研究进展}

📄 完整报告：{飞书文档链接}
```

### 第四步：推送到三个群聊

使用 `feishu_send_message` 工具，依次向三个群聊发送三条消息：

```
对于每个群聊 (chat_id):
  对于每段消息:
    feishu_send_message(
      receive_id: chat_id,
      receive_id_type: "chat_id",
      content: 消息内容,
      msg_type: "text"
    )
```

## 摘要生成规则

- 摘要控制在 3-5 句话以内
- 突出**变化**和**新增**，不重复已知信息
- 使用中文，保留英文术语
- 对比前一日数据（如有），标注升降趋势
- 国内厂商表现单独提及

## 错误处理

- 如果某个群聊发送失败，记录错误并继续发送其他群聊
- 如果文档更新失败，仍然发送基于上次数据的摘要
- 所有错误记录到日志

## 手动触发

用户说"推送技术雷达"、"发送今日报告"等自然语言时，执行此流程。
