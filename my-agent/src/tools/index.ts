/**
 * 工具注册表：在这里汇总 agent 可用的全部工具。
 */
import type { AgentTool } from "@mariozechner/pi-agent-core";
import { echoTool } from "./echo.js";

export const tools: AgentTool<any>[] = [
  echoTool,
  // TODO: 在这里加入你的自定义工具
];
