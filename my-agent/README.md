# my-agent

基于 [pi agent 框架](https://github.com/badlogic/pi-mono)（`pi-agent-core` + `pi-ai`）的自定义 agent 脚手架。

## 结构

```
src/
  index.ts        CLI 入口（交互 REPL / 单次提问）
  agent.ts        Agent 装配：system prompt + model + tools
  llm/index.ts    LLM 接口层（⚠️ 占位，待接入 —— 见文件内参考实现注释）
  tools/          工具注册表：pi-coding-agent 的 read/write/edit/bash/grep/find/ls + 自定义工具
    echo.ts       示例工具
    index.ts      注册表（工作目录 = AGENT_WORKSPACE 或进程 cwd，serve.py 会设为 My 根目录）
```

## 与语音通道的集成

`serve.py`（My 根目录）收到语音 → 本地 Whisper 转文字 → 调用
`node my-agent/dist/index.js <prompt>` 处理 inbox。改动后需重启 serve.py 生效。

## 运行

```bash
npm install
npm run dev              # 交互模式
npm run dev -- "你好"     # 单次提问
npm run typecheck        # 类型检查
```

## 待办：接入 LLM

当前运行会抛出 `[my-agent] LLM 接口尚未接入`。打开 `src/llm/index.ts`，
在 `createModel()` 里按注释中的参考实现用 pi-ai 的 `getModel()` 返回模型句柄即可，
其余代码无需改动。配置通过环境变量传入（见 `.env.example`）：

- `AGENT_LLM_PROVIDER` — provider 名（anthropic / openai / google / groq ...）
- `AGENT_LLM_MODEL` — 模型 id
- `AGENT_LLM_API_KEY` / `AGENT_LLM_BASE_URL` — 可选

## 加新工具

在 `src/tools/` 下新建文件，导出 `AgentTool`（参考 `echo.ts`），
然后在 `src/tools/index.ts` 的 `tools` 数组里注册。
