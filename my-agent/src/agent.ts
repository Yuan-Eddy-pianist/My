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

  // 循环熔断：同一工具 + 同样参数连续调用，第 3 次起拦截，
  // 把"你在重复自己"作为错误结果回给模型，逼它换策略或直接收尾。
  // （2026-09-01 failed case：read 同参循环 140+ 次，KV cache 涨到 18GB）
  let lastSig = "";
  let repeatCount = 0;

  return new Agent({
    initialState: {
      systemPrompt: options.systemPrompt ?? SYSTEM_PROMPT,
      model,
      tools: createTools(workspace),
    },
    // 本地 vLLM 不校验 key；换远端 provider 时从 AGENT_LLM_API_KEY 取
    getApiKey: () => resolveApiKey(llmConfig),
    beforeToolCall: async ({ toolCall, args }) => {
      const sig = `${toolCall.name}:${JSON.stringify(args)}`;
      if (sig === lastSig) {
        repeatCount += 1;
      } else {
        lastSig = sig;
        repeatCount = 1;
      }
      if (repeatCount >= 3) {
        return {
          block: true,
          reason:
            `Blocked: you have already called "${toolCall.name}" with these exact ` +
            `arguments ${repeatCount} times and received the result each time. ` +
            "Do NOT repeat the same call. Use the result you already have, " +
            "take a different action (e.g. write the target file), or finish now.",
        };
      }
      return undefined;
    },
  });
}
