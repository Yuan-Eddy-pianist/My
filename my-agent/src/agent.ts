/**
 * Agent 装配：系统提示词 + 模型 + 工具。
 * 模型默认走本地 vLLM（见 src/llm），工具含 pi-coding-agent 的文件/Shell 工具。
 */
import { Agent } from "@mariozechner/pi-agent-core";
import {
  createModel,
  loadLlmConfig,
  resolveApiKey,
  type LlmConfig,
} from "./llm/index.js";
import { createTools, resolveWorkspace } from "./tools/index.js";

export const SYSTEM_PROMPT = `你是 my-agent，一个基于 pi agent 框架的自定义 agent。
- 回答简洁、直接，必要时使用工具。
- 不确定时说明不确定，不要编造。`;

export interface CreateAgentOptions {
  /** 覆盖默认的 LLM 配置（否则读环境变量） */
  llm?: Partial<LlmConfig>;
  /** 覆盖系统提示词 */
  systemPrompt?: string;
  /** 工具的工作目录（默认 AGENT_WORKSPACE 或进程 cwd） */
  workspace?: string;
}

export function createAgent(options: CreateAgentOptions = {}): Agent {
  const llmConfig = { ...loadLlmConfig(), ...options.llm };
  const model = createModel(llmConfig);
  const workspace = options.workspace ?? resolveWorkspace();

  return new Agent({
    initialState: {
      systemPrompt: options.systemPrompt ?? SYSTEM_PROMPT,
      model,
      tools: createTools(workspace),
    },
    // 本地 vLLM 不校验 key；换远端 provider 时从 AGENT_LLM_API_KEY 取
    getApiKey: () => resolveApiKey(llmConfig),
  });
}
