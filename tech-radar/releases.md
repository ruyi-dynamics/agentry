# 子命令：releases — 最新模型发布动态

## 搜索目标

搜索近期发布的AI模型和重大更新，按类别和厂商两条线交叉扫描。

---

## 一、按模型类别

### 1. LLM 大语言模型
- 搜索关键词：`new LLM release 2026`, `latest language model announcement`, `AI model launch 2026`
- 关注：新模型首发、重大版本更新、开源模型发布

### 2. 多模态模型
- 搜索关键词：`multimodal model release 2026`, `vision language model latest`, `omni model 2026`
- 关注：视觉-语言模型、全模态模型、图文理解/生成

### 3. 语音模型 (STT / TTS / S2S)
- 搜索关键词：`speech model release 2026`, `TTS new model announcement`, `voice AI latest`, `S2S speech model`
- 关注：语音识别、语音合成、端到端语音对话

### 4. 推理/代码模型
- 搜索关键词：`reasoning model release 2026`, `code model latest`, `coding AI model`
- 关注：o-系列推理模型、代码生成、数学推理

### 5. 机器人/具身智能模型
- 搜索关键词：`robot model release 2026`, `embodied AI announcement`, `humanoid robot AI latest`
- 关注：通用机器人策略、人形机器人、灵巧操作

### 6. 自动驾驶模型
- 搜索关键词：`autonomous driving model release 2026`, `self-driving AI announcement`
- 关注：端到端驾驶、世界模型、感知-规划一体化

---

## 二、按厂商覆盖

搜索时按厂商逐个跟踪，确保不遗漏：

### 🇺🇸 海外厂商

| 厂商 | 代表模型 | 搜索关键词 |
|------|----------|------------|
| **OpenAI** | GPT-5, o3/o4, DALL-E, Whisper | `OpenAI new model release 2026` |
| **Google / DeepMind** | Gemini 2.5, Gemma | `Google Gemini new release 2026` |
| **Anthropic** | Claude 4 (Opus/Sonnet/Haiku) | `Anthropic Claude new model 2026` |
| **Meta** | Llama 4, Segment Anything | `Meta Llama new release 2026` |
| **Mistral** | Mistral Large, Codestral | `Mistral new model 2026` |
| **xAI** | Grok | `xAI Grok new model 2026` |
| **ElevenLabs** | TTS, Voice Clone | `ElevenLabs new TTS model 2026` |

### 🇨🇳 国内厂商

| 厂商 | 代表模型 | 搜索关键词 |
|------|----------|------------|
| **阿里 / 通义** | Qwen 3, Qwen-VL, Qwen-Audio, CosyVoice | `Qwen new model release 2026`, `阿里通义新模型` |
| **字节 / 豆包** | Doubao Seed, Coze | `字节豆包新模型 2026`, `Doubao Seed release` |
| **智谱 / GLM** | GLM-5, GLM-4, CogVideo, CogView | `智谱GLM新模型 2026`, `GLM new model release` |
| **MiniMax** | MiniMax-M2.5, MiniMax-Text, 海螺AI | `MiniMax new model release 2026`, `MiniMax海螺新模型` |
| **月之暗面 / Kimi** | Kimi K2.5, Kimi k1.5 | `Kimi new model release 2026`, `月之暗面新模型` |
| **DeepSeek** | DeepSeek V3, DeepSeek R1, DeepSeek Coder | `DeepSeek new model release 2026`, `深度求索新模型` |
| **百度 / 文心** | ERNIE 4.5, 文心大模型 | `百度文心新模型 2026`, `ERNIE new model` |
| **小米 / MiMo** | MiMo V2.5, MiMo TTS | `Xiaomi MiMo new model 2026`, `小米MiMo新模型` |
| **华为 / 盘古** | 盘古大模型, 华为云 | `华为盘古新模型 2026`, `Huawei Pangu model` |
| **科大讯飞** | 星火大模型, Spark | `科大讯飞星火新模型 2026`, `iFlytek Spark release` |
| **零一万物** | Yi, Yi-Lightning | `零一万物新模型 2026`, `Yi model release` |
| **面壁智能** | MiniCPM, CPM | `面壁智能MiniCPM 2026`, `MiniCPM new release` |
| **商汤** | 日日新 SenseNova | `商汤日日新 2026`, `SenseNova new model` |
| **昆仑万维** | 天工大模型 | `昆仑万维天工 2026` |
| **百川智能** | Baichuan | `百川智能新模型 2026`, `Baichuan release` |

---

## 三、搜索流程

### 第一步：时间限定搜索

搜索最近 1-2 周的发布动态：

```
WebSearch: "new AI model release April 2026"
WebSearch: "latest LLM announcement 2026 this week"
WebSearch: "new TTS STT speech model release 2026"
WebSearch: "AI model launch this week April 2026"
```

### 第二步：厂商逐个跟踪

```
# 海外
WebSearch: "OpenAI GPT new release April 2026"
WebSearch: "Google Gemini new model April 2026"
WebSearch: "Anthropic Claude new model 2026"
WebSearch: "Meta Llama 4 release 2026"

# 国内
WebSearch: "智谱GLM-5 new release 2026"
WebSearch: "MiniMax M2.5 new model 2026"
WebSearch: "Kimi K2.5 new release 2026"
WebSearch: "DeepSeek new model April 2026"
WebSearch: "Qwen 3 new release 2026"
WebSearch: "小米MiMo V2.5 new model 2026"
WebSearch: "百度文心ERNIE 4.5 2026"
WebSearch: "科大讯飞星火新模型 2026"
WebSearch: "零一万物Yi new model 2026"
WebSearch: "面壁智能MiniCPM new release 2026"
WebSearch: "百川智能Baichuan 2026"
```

### 第三步：详情获取

- 对重大发布使用 WebFetch 获取官方博客/公告详情
- 对比前代模型的关键提升（参数量、性能、新能力）

---

## 四、输出格式

```markdown
### 🚀 最新发布 — {日期范围}

#### 🔥 本周重大发布

**海外**
- **{模型名称}** — {厂商} ({发布日期})
  {一句话描述}
  影响：{简要评估}
  📎 {URL}

**国内**
- **{模型名称}** — {厂商} ({发布日期})
  {一句话描述}
  影响：{简要评估}
  📎 {URL}

#### 📋 值得关注的更新
- **{模型名称}** — {厂商} | {一句话描述}
  📎 {URL}

#### 🔮 即将发布 (传闻/预告)
- **{模型/项目}** — {厂商} | {传闻来源}
  📎 {URL}

---
📊 本期覆盖 {N} 家厂商，发现 {M} 项发布/更新
```

---

## 五、搜索策略

- 如用户只关心特定类别或厂商，只搜索该范围；否则全部扫描
- 国内外分开呈现，方便对比
- 重大发布（新模型首发、版本大升级）优先展示
- 关注开源 vs 闭源的区分
- 对比前代模型的关键指标变化（如有）
