/**
 * Agent 装配：系统提示词 + 模型 + 工具。
 * 模型来自 src/llm（尚未接入），其余部分已经可用。
 */
import { Agent } from "@mariozechner/pi-agent-core";
import { createModel, loadLlmConfig, type LlmConfig } from "./llm/index.js";
import { tools } from "./tools/index.js";

export const SYSTEM_PROMPT = `你是 my-agent，一个基于 pi agent 框架的自定义 agent。
- 回答简洁、直接，必要时使用工具。
- 不确定时说明不确定，不要编造。`;

export interface CreateAgentOptions {
  /** 覆盖默认的 LLM 配置（否则读环境变量） */
  llm?: Partial<LlmConfig>;
  /** 覆盖系统提示词 */
  systemPrompt?: string;
}

export function createAgent(options: CreateAgentOptions = {}): Agent {
  const model = createModel({ ...loadLlmConfig(), ...options.llm });

  return new Agent({
    initialState: {
      systemPrompt: options.systemPrompt ?? SYSTEM_PROMPT,
      model,
      tools,
    },
  });
}
