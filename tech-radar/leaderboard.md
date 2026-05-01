# 子命令：leaderboard — 模型排行榜

## 搜索目标

搜索各大模型排行榜的最新状态，覆盖以下类别：

### 排行榜类别

1. **LLM 大语言模型**
   - 搜索关键词：`LLM leaderboard 2026`, `best LLM ranking`, `chatbot arena leaderboard`
   - 关注平台：Chatbot Arena (LMSYS), OpenCompass, SuperCLUE, MMLU, HumanEval
   - 关注模型：GPT-5, Claude 4, Gemini 2.5, Qwen 3, DeepSeek V3, Llama 4, MiMo

2. **STT 语音识别**
   - 搜索关键词：`STT model ranking 2025 2026`, `speech recognition benchmark`, `ASR leaderboard`
   - 关注：Whisper, Conformer, Paraformer, SenseVoice, Qwen-Audio
   - 指标：WER (Word Error Rate), 中文/英文/多语言识别准确率

3. **TTS 语音合成**
   - 搜索关键词：`TTS model ranking 2025 2026`, `text to speech benchmark`, `best TTS model`
   - 关注：CosyVoice, ChatTTS, Fish Speech, VALL-E, Bark, ElevenLabs
   - 指标：MOS (Mean Opinion Score), 自然度, 多语言支持

4. **S2S 语音对话 (Speech-to-Speech)**
   - 搜索关键词：`S2S speech to speech model 2025 2026`, `end-to-end speech model`, `voice AI model ranking`
   - 关注：GPT-4o-audio, Gemini Live, MiMo TTS, Qwen-Audio, Moshi
   - 指标：延迟, 自然度, 多轮对话能力

### 搜索流程

1. **搜索排行榜**：对每个类别执行 WebSearch
2. **抓取排名**：对主要排行榜页面使用 WebFetch 获取详细排名
3. **对比分析**：整理 Top 10 模型，标注关键指标变化

### 输出格式

```markdown
### 🏆 模型排行榜

#### LLM 大语言模型
| 排名 | 模型 | 厂商 | 关键指标 | 来源 |
|------|------|------|----------|------|
| 1 | ... | ... | ... | {URL} |

#### STT 语音识别
| 排名 | 模型 | 厂商 | WER (EN) | WER (ZH) | 来源 |
|------|------|------|----------|----------|------|
| 1 | ... | ... | ... | ... | {URL} |

#### TTS 语音合成
| 排名 | 模型 | 厂商 | 自然度 | 多语言 | 来源 |
|------|------|------|--------|--------|------|
| 1 | ... | ... | ... | ... | {URL} |

#### S2S 语音对话
| 排名 | 模型 | 厂商 | 延迟 | 自然度 | 来源 |
|------|------|------|------|--------|------|
| 1 | ... | ... | ... | ... | {URL} |
```

### 搜索策略

```
WebSearch: "LLM leaderboard chatbot arena 2026 ranking"
WebSearch: "best LLM model 2026 benchmark comparison"
WebSearch: "STT ASR speech recognition benchmark ranking 2025 2026"
WebSearch: "TTS text to speech model ranking benchmark 2025 2026"
WebSearch: "S2S speech to speech end-to-end voice model 2025 2026"
WebSearch: "opencompass superclue LLM ranking 2026"
```

如用户只关心特定类别，只搜索该类别；否则全部扫描。
