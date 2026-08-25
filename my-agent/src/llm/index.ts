/**
 * LLM 接口层 —— 目前只是占位，等你接入具体的模型配置。
 *
 * pi-ai 提供了统一的多 provider 模型句柄，典型用法：
 *
 *   import { getModel } from "@mariozechner/pi-ai";
 *   const model = getModel("anthropic", "claude-sonnet-4-5");
 *   // 或 getModel("openai", "gpt-5"), getModel("google", "gemini-2.5-pro") ...
 *
 * 接入时只需实现 createModel()，返回 pi-ai 的 Model 即可，
 * agent / CLI 侧不需要改动。
 */

export interface LlmConfig {
  /** provider 名称，如 "anthropic" | "openai" | "google" | "groq" ... */
  provider: string;
  /** 模型 id，如 "claude-sonnet-4-5" */
  model: string;
  /** API key（也可以交给 pi-ai 读环境变量，如 ANTHROPIC_API_KEY） */
  apiKey?: string;
  /** 自定义 base URL（自建网关 / 代理时用到） */
  baseUrl?: string;
}

/** 从环境变量读取默认配置（可被 CLI 参数覆盖） */
export function loadLlmConfig(): LlmConfig {
  return {
    provider: process.env.AGENT_LLM_PROVIDER ?? "",
    model: process.env.AGENT_LLM_MODEL ?? "",
    apiKey: process.env.AGENT_LLM_API_KEY,
    baseUrl: process.env.AGENT_LLM_BASE_URL,
  };
}

/**
 * TODO: 接入 LLM。
 *
 * 参考实现（取消注释并按需调整）：
 *
 *   import { getModel, type Model } from "@mariozechner/pi-ai";
 *
 *   export function createModel(config: LlmConfig = loadLlmConfig()): Model<any> {
 *     if (!config.provider || !config.model) {
 *       throw new Error("请设置 AGENT_LLM_PROVIDER 和 AGENT_LLM_MODEL");
 *     }
 *     const model = getModel(config.provider as any, config.model as any);
 *     // 如需自定义 apiKey / baseUrl，可在这里覆盖 model 的对应字段
 *     return model;
 *   }
 */
export function createModel(_config: LlmConfig = loadLlmConfig()): never {
  throw new Error(
    "[my-agent] LLM 接口尚未接入：请在 src/llm/index.ts 的 createModel() 中 " +
      "用 pi-ai 的 getModel() 返回模型句柄（文件内有参考实现注释）。",
  );
}
