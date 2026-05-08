# English Speaking Practice (Python Version)

基于 Python tkinter 的英语口语练习桌面应用。集成 DeepSeek 大模型、阿里云发音评测、whisper.cpp 语音识别和 edge-tts 神经语音合成。从 Java Swing 版本完整移植。

---

## 功能

| 模块 | 说明 |
|------|------|
| **Reading Test** | 朗读英文文章 → AI 评测发音、流利度 → 教练式反馈 + 音素级评分 |
| **Conversation Practice** | 情景对话（面试/聊天/求助），支持 Hide Text 听力训练模式 |
| **Voice Input** | 麦克风录音，whisper.cpp 实时转文字 |
| **Voice Output** | edge-tts 神经语音朗读，7 种声线 + 5 档语速可调 |
| **Pronunciation Assessment** | 阿里云音素级发音评测（可选，未配置时自动降级） |
| **Typing Animation** | AI 回复打字机逐字跳出，与语音同步 |
| **Warm UI** | ttk 暖色主题，圆角组件，奶油背景 + 琥珀强调色 |

---

## 技术架构

```
用户录音 → whisper.cpp (STT) + 阿里云 (发音评测)
                ↓
         DeepSeek API (教练反馈 / 对话回复)
                ↓
         edge-tts (神经语音朗读) → 扬声器
```

### 技术栈一览

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **语言** | Python | ≥ 3.10 | 主语言 |
| **GUI** | tkinter (ttk) | 内置 | 桌面界面框架，clam 暖色主题 |
| **HTTP** | requests | ≥ 2.28 | DeepSeek API + 阿里云 Token 获取 |
| **WebSocket** | websocket-client | ≥ 1.6 | 阿里云实时发音评测 |
| **音频采集** | sounddevice + NumPy | ≥ 0.4.6 | 麦克风录音 (16kHz/16-bit/Mono) |
| **语音识别** | whisper.cpp | — | 本地 STT，调用预编译 `whisper-cli.exe` |
| **语音合成** | edge-tts | ≥ 6.1 | 微软神经语音，调用 `edge-playback` CLI |
| **序列化** | json (内置) | — | JSON 解析 |
| **并发** | threading (内置) | — | 后台 API 调用，不阻塞 UI |
| **AI** | DeepSeek API | — | 教练反馈 + 对话生成 |
| **发音评测** | 阿里云智能语音 | — | 音素级发音评分（可选） |

### 与 Java 版本对比

| 维度 | Java 版本 | Python 版本 |
|------|-----------|-------------|
| GUI 框架 | Swing + FlatLaf | tkinter + ttk (clam theme) |
| HTTP 客户端 | java.net.http.HttpClient | requests |
| WebSocket | java.net.http.WebSocket | websocket-client |
| JSON | Gson | json (built-in) |
| 音频录制 | javax.sound.sampled | sounddevice |
| TTS | edge-playback (subprocess) | edge-playback (subprocess) |
| STT | whisper-cli.exe (subprocess) | whisper-cli.exe (subprocess) |
| 并发 | SwingWorker | threading.Thread |
| 模型层 | POJO (getter/setter) | @dataclass |
| 枚举 | Java enum | Python Enum |

---

## 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

依赖清单 (`requirements.txt`)：

```
requests>=2.28.0       # HTTP 请求（DeepSeek API + 阿里云 Token）
websocket-client>=1.6.0 # WebSocket（阿里云发音评测）
sounddevice>=0.4.6     # 麦克风录音（跨平台）
numpy>=1.24.0          # 音频数据处理
edge-tts>=6.1.0        # 语音合成（提供 edge-playback 命令）
```

> **注意**：`sounddevice` 在 Linux 上需要 `libportaudio2`；在 macOS 上需要 `portaudio`。

### 2. 准备 whisper.cpp（语音识别）

```bash
# 下载 whisper.cpp 预编译包，放入 STT/ 目录
# ggml-base.en.bin (~141MB): https://huggingface.co/ggerganov/whisper.cpp
# whisper-bin-x64.zip: https://github.com/ggml-org/whisper.cpp/releases
# 解压后将 whisper-cli.exe、ggml.dll 等放入 STT/

# 目录结构:
python_ver/
└── STT/
    ├── whisper-cli.exe
    ├── ggml-base.bin
    ├── ggml.dll
    └── ...
```

如果已安装 Java 版本，whisper.cpp 会自动从 `../Eng_verbal_practice_tool/STT/` 发现。

### 3. 获取 API Key

- **DeepSeek**：https://platform.deepseek.com
- **阿里云 ASR（可选）**：开通智能语音交互服务，获取 AccessKey ID/Secret 和 AppKey

### 4. 运行

```bash
cd python_ver
python main.py
```

首次启动显示 API 配置页。之后通过主界面 **API Settings** 按钮修改。

---

## 使用说明

### Reading Test
1. 看文章 → 点 **🎤 Record** 朗读（或打字）
2. 点 **Evaluate** → AI 返回评分 + 反馈 + 发音详情
3. **🔊 TTS** 控制播放，**🔁 Replay** 重听

### Conversation Practice
1. 选择场景（面试/聊天/求助）和回复长度（Normal/Detailed）
2. 点 **Start** → AI 开始对话
3. 录音回复 → 打字机动画 + 语音同步播出
4. **🙈 Hide Text** — 隐藏 AI 文字，纯听力训练
5. **Summary** — 对话结束后，查看整场发音分析

---

## 项目结构

```
python_ver/
├── main.py                          — 应用入口 + 暖色主题 + 面板路由
├── config.properties                 — API 密钥配置（不入 git）
├── texts.txt                         — 朗读语料库（5 篇英文短文）
├── requirements.txt                  — Python 依赖
├── model/
│   ├── scenario.py                   — 场景枚举（面试/聊天/求助）
│   ├── reading_result.py             — 朗读评测结果 @dataclass
│   ├── pronunciation_result.py       — 发音评测结果 + PhonemeScore + WordScore
│   └── conversation_turn.py          — 对话轮次记录
├── service/
│   ├── ai_service.py                 — DeepSeek API 调用
│   ├── alibaba_asr_service.py        — 阿里云发音评测（WebSocket + Token 管理）
│   ├── reading_service.py            — 朗读评测逻辑（ASR + AI 教练反馈）
│   ├── conversation_service.py       — 对话管理 + 发音总结 + 回复长度控制
│   ├── audio_recorder.py             — 麦克风录音（sounddevice, 16kHz WAV）
│   ├── speech_to_text.py             — whisper.cpp 调用
│   └── text_to_speech.py             — edge-tts 语音合成（7 声线 + 5 语速）
└── gui/
    ├── setup_panel.py                — API 配置页（首次启动）
    ├── home_panel.py                 — 主菜单 + API Settings 入口
    ├── reading_panel.py              — 朗读测试界面
    └── conversation_panel.py         — 对话界面（打字机/隐藏文字/加载动画）
```

### 各层职责

| 层 | 职责 |
|----|------|
| **model/** | 纯数据类（`@dataclass`），不包含业务逻辑 |
| **service/** | 封装业务逻辑 + 外部 API 调用，与 GUI 解耦 |
| **gui/** | tkinter 界面组件，每个 Panel 自包含其状态 |
| **main.py** | 应用生命周期管理、面板路由、暖色主题配置 |

---

## 配置说明

`config.properties` 格式：

```properties
api.endpoint=https://api.deepseek.com/v1/chat/completions
api.key=sk-xxxxxxxx          # DeepSeek API Key（必填）
api.model=deepseek-chat
aliyun.accessKeyId=xxxxxx    # 阿里云 AccessKey ID（可选）
aliyun.accessKeySecret=xxxx  # 阿里云 AccessKey Secret（可选）
aliyun.appKey=xxxxxx         # 阿里云 AppKey（可选）
```

### 降级策略

| 场景 | 行为 |
|------|------|
| 阿里云未配置 | `enabled=False`，评测自动降级为 whisper + DeepSeek |
| 阿里云 Token 获取失败 | 返回 None → 降级 |
| WebSocket 连接超时 | 返回 None → 降级 |
| 麦克风不可用 | 抛出异常，界面提示，可继续打字输入 |
| whisper.cpp 不存在 | 抛出异常，界面提示安装路径 |

---

## 注意事项

- `config.properties` 应加入 `.gitignore`，避免提交 API 密钥
- `edge-tts` 需要网络连接调用微软云端语音引擎
- whisper.cpp 首次运行需下载模型文件（~141MB base 模型）
- 仅在 Windows 下测试（依赖 `edge-playback` CLI），Linux/macOS 可能需调整 TTS 方案
- 建议使用 Python ≥ 3.10（`@dataclass` + `str | None` 类型语法）
