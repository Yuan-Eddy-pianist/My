/**
 * 工具注册表：汇总 agent 可用的全部工具。
 *
 * - coding tools：复用 pi-coding-agent 的 read / write / edit / bash / grep / find / ls，
 *   工作目录默认取进程 cwd（serve.py 调用时会设为 My 工作区根目录），
 *   也可用 AGENT_WORKSPACE 环境变量覆盖。
 * - 自定义工具：照 echo.ts 的结构加，然后在下方数组注册。
 */
import path from "node:path";
import type { AgentTool } from "@mariozechner/pi-agent-core";
import { createCodingTools } from "@mariozechner/pi-coding-agent";
import { echoTool } from "./echo.js";

export function resolveWorkspace(): string {
  return path.resolve(process.env.AGENT_WORKSPACE ?? process.cwd());
}

export function createTools(cwd: string = resolveWorkspace()): AgentTool<any>[] {
  return [
    ...(createCodingTools(cwd) as AgentTool<any>[]),
    echoTool,
    // TODO: 在这里加入你的自定义工具
  ];
}
