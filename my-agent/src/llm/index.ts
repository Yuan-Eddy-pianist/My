/**
 * LLM 接口层。
 *
 * 默认走本地 vLLM（OpenAI-compatible chat completions）：
 *   http://127.0.0.1:8800/v1 ，模型 id 从 /v1/models 自动探测（默认 deepseek-v4-flash）。
 * 本地 vLLM 不校验 key，返回占位 "EMPTY" 即可。
 *
 * 如需换成其他 provider（如 OpenRouter），用 pi-ai 的 getModel()：
 *
 *   import { getModel } from "@mariozechner/pi-ai";
 *   const model = getModel("openrouter", "anthropic/claude-sonnet-4.5");
 *   // key 由 agent.ts 里的 getApiKey 注入（读 AGENT_LLM_API_KEY / my-agent/.env）
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Model } from "@mariozechner/pi-ai";

export interface LlmConfig {
  /** provider 名称（本地 vLLM 时为 "vllm-local"） */
  provider: string;
  /** 模型 id */
  model: string;
  /** API key（本地 vLLM 不需要，留空即可） */
  apiKey?: string;
  /** OpenAI-compatible base URL */
  baseUrl?: string;
  /** 上下文窗口 */
  contextWindow?: number;
  /** 最大输出 token */
  maxTokens?: number;
}

const DEFAULTS: LlmConfig = {
  provider: "vllm-local",
  model: "deepseek-v4-flash",
  baseUrl: "http://127.0.0.1:8800/v1",
  contextWindow: 131072,
  maxTokens: 8192,
};

/** 轻量 .env 读取（my-agent/.env），不覆盖已有环境变量 */
function loadDotEnv(): void {
  const envPath = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "../../.env",
  );
  if (!fs.existsSync(envPath)) return;
  for (const raw of fs.readFileSync(envPath, "utf8").split("\n")) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const idx = line.indexOf("=");
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim().replace(/^['"]|['"]$/g, "");
    if (key && !(key in process.env)) process.env[key] = value;
  }
}

/** 从环境变量读取配置（缺省回落到本地 vLLM 默认值） */
export function loadLlmConfig(): LlmConfig {
  loadDotEnv();
  return {
    provider: process.env.AGENT_LLM_PROVIDER ?? DEFAULTS.provider,
    model: process.env.AGENT_LLM_MODEL ?? DEFAULTS.model,
    apiKey: process.env.AGENT_LLM_API_KEY,
    baseUrl: process.env.AGENT_LLM_BASE_URL ?? DEFAULTS.baseUrl,
    contextWindow: process.env.AGENT_LLM_CONTEXT_WINDOW
      ? Number(process.env.AGENT_LLM_CONTEXT_WINDOW)
      : DEFAULTS.contextWindow,
    maxTokens: process.env.AGENT_LLM_MAX_TOKENS
      ? Number(process.env.AGENT_LLM_MAX_TOKENS)
      : DEFAULTS.maxTokens,
  };
}

/**
 * 创建模型句柄。当前实现：本地 vLLM（OpenAI-compatible）。
 * 换远端 provider 时在这里改为 getModel(provider, modelId)。
 */
export function createModel(
  config: LlmConfig = loadLlmConfig(),
): Model<"openai-completions"> {
  if (!config.baseUrl) {
    throw new Error("[my-agent] 缺少 baseUrl：请设置 AGENT_LLM_BASE_URL");
  }
  return {
    id: config.model,
    name: `${config.model} (${config.provider})`,
    api: "openai-completions",
    provider: config.provider,
    baseUrl: config.baseUrl,
    reasoning: false,
    input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: config.contextWindow ?? 131072,
    maxTokens: config.maxTokens ?? 8192,
  };
}

/** 提供给 Agent 的 getApiKey：本地 vLLM 不需要 key，返回占位值 */
export function resolveApiKey(config: LlmConfig = loadLlmConfig()): string {
  return config.apiKey ?? "EMPTY";
}
