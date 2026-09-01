# My 语音工作台 — 实施 Plan（交接用）

> 写于 2026-09-01。背景：上一轮的语音反馈 UI 实现与预期有差距，本文件记录已确定的方向、
> 当前系统状态和待办，供新会话直接接手实现。相关代码改动目前**未提交**（见文末）。

## 1. 系统架构（现状，全部本地）

```
app/index.html 录音（番茄钟+麦克风页面）
  → POST /api/voice → serve.py (127.0.0.1:8765)
  → 本地 Whisper 转写（MLX, mlx-community/whisper-medium-mlx）
  → data/inbox.md 追加 → 队列
  → node my-agent/dist/index.js <prompt>   ← pi agent 框架（pi-agent-core + pi-ai）
  → 本地 LLM: Qwen3-30B-A3B-Instruct-2507-4bit（mlx-lm server, 127.0.0.1:8800）
  → 更新 data/todos.json（projects / tasks / reminders）
```

- 启动：`./start.sh`（会同时拉起 whisper 服务、mlx-lm LLM 服务、serve.py；LLM 模型在 `models/`）
- 每日 18:00 自动巡检：`serve.py` 内 `progress_scheduler_loop`，遍历 active 项目跑 `git log/status` 更新 `progress` 字段；手动触发 `POST /api/progress`
- 看板页面：`app/todos.html`（done 项目已从主列表隐藏，可点「已完成 N」展开）
- agent 状态接口：`GET /api/agent` → `{state: idle|transcribing|queued|running|done|error, message, lastNote, lastResult, voicePending, agentPending}`

## 2. 本次要重做的功能：语音发送后的反馈提示

**已确认的设方向（用户明确选择，勿再改方向）：**

只要一个轻提示，不要信息堆砌：

1. **麦克风按钮变"思考球"**：发送语音后，mic 按钮原地进入呼吸/脉冲状态（类比 Siri 的听→想→点头），下方只显示一行极简阶段文字：
   `上传中… → 转写中… → AI 整理中… → 已完成 ✓`（完成后短暂停留即消失；出错显示红色错误）
2. **钟表呼吸（环境光与钟表结合，不是页面边缘）**：agent 工作期间，番茄钟表盘缓慢呼吸发光（约 3~4 秒一周期的柔和 glow），结束即停。要克制、有美感，不能影响计时功能。

**状态映射数据源**：`/api/agent` 轮询（app.js 已有 `fetchAgentStatus` + 900ms 轮询机制）：
- `voicePending > 0` 或 `state=transcribing` → 转写中
- `state=queued` → 排队中；`state=running` → AI 整理中
- `done` → 已完成 ✓（仅当之前处于 busy 时才提示，避免页面加载时误闪）
- 录音中（`listening`）不覆盖录音状态

## 3. 上一轮实现（未提交，可供参考或直接重写）

改动文件（`git diff` 可见）：
- `app/app.js`：`setupVoice` 新增 `faceEl` 参数、`setThinking()`、`wasBusy` 转换检测、enqueue 时即时反馈
- `app/index.html`：setupVoice 传入 `faceEl: $(".clock-face")`
- `app/styles.css`：`.btn-mic.thinking`（breathe-btn 动画）、`.clock-face.breathing .clock-dial`（drop-shadow 呼吸）

**用户反馈：与预期差别较大。** 新会话应先让用户描述具体哪里不对（动画形态？时机？文字？），
或用浏览器截图对齐预期后再动手。验证方式：发一条真实语音或
`curl -X POST 127.0.0.1:8765/api/inbox -d '{"text":"测试"}'`，观察状态流转。

## 4. 已知问题（顺带修）

1. **本地模型慢，复合请求会超时**：serve.py 超时已从 300s 提到 900s（未提交）。
   AGENT_PROMPT 已加规则：inbox 里的重型请求（写周报、批量 inspect 仓库）**不执行**，
   只记录为 task（未提交）。上周积压已部分处理（"回邮件"任务已入库；周报请求应该已变成 task——请核对）。
2. **inbox 积压**：data/inbox.md 若还有未处理内容，新会话可先触发一次处理验证链路。
3. **UI 视觉验证缺失**：上一轮无法调用浏览器工具，动画效果未经真实浏览器确认——这次必须截图验证。
4. **Failed case（2026-09-01）**："提醒我待会补卡"这种单句任务，本地 Qwen3-30B 跑两遍
   （含 verify 重试）均未落地任何文件，单次几分钟高负载后被手动停掉、人工补录。
   结论：简单任务也不应依赖本地 30B；长期方案是 `my-agent/.env` 切回服务器 DeepSeek（改 3 行），
   本地模型仅离线备用。证据见 data/serve.log 与 git 历史（48cee8c 前后的 verify 机制）。

## 5. 关键文件地图

| 文件 | 作用 |
|---|---|
| `serve.py` | 服务器：语音/Whisper/队列/agent 调用/每日巡检。提示词在 `AGENT_PROMPT`、`PROGRESS_PROMPT` |
| `my-agent/` | pi 框架 agent（TS）。`src/llm/index.ts` 模型配置、`src/agent.ts` 装配、`src/tools/` 工具 |
| `my-agent/.env` | `AGENT_LLM_*`：当前指向本地 8800；切回服务器 DeepSeek 改 3 行即可 |
| `app/app.js` | 前端逻辑（setupVoice / setupPomodoro / 轮询） |
| `app/styles.css` | 样式，主题色 `--accent: #37995e` 绿 |
| `data/todos.json` | 工作区数据；`data/.agent-status.json`  agent 状态 |

## 6. 完成后

- `git add -A && git commit`（上次 UI + serve.py 改动均未提交）
- 模型/日志不入库：`models/`、`data/tmp/`、`data/serve.log` 已在 .gitignore
