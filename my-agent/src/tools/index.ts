/**
 * 工具注册表：汇总 agent 可用的全部工具。
 *
 * - coding tools：复用 pi-coding-agent 的 read / write / edit / bash / grep / find / ls，
 *   工作目录默认取进程 cwd（serve.py 调用时会设为 My 工作区根目录），
 *   也可用 AGENT_WORKSPACE 环境变量覆盖。
 * - 自定义工具：照 echo.ts 的结构加，然后在下方数组注册。
 */
import {
  access,
  mkdir,
  open,
  readFile,
  rename,
  rm,
} from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import type { AgentTool } from "@mariozechner/pi-agent-core";
import { createCodingTools } from "@mariozechner/pi-coding-agent";
import { echoTool } from "./echo.js";

export function resolveWorkspace(): string {
  return path.resolve(process.env.AGENT_WORKSPACE ?? process.cwd());
}

/** Replace files atomically so the web server never observes a truncated JSON write. */
async function atomicWriteFile(absolutePath: string, content: string): Promise<void> {
  const dir = path.dirname(absolutePath);
  await mkdir(dir, { recursive: true });
  const temporaryPath = path.join(
    dir,
    `.${path.basename(absolutePath)}.${process.pid}.${randomUUID()}.tmp`,
  );
  let handle;
  try {
    handle = await open(temporaryPath, "wx");
    await handle.writeFile(content, "utf8");
    await handle.sync();
    await handle.close();
    handle = undefined;
    await rename(temporaryPath, absolutePath);
  } finally {
    await handle?.close().catch(() => {});
    await rm(temporaryPath, { force: true }).catch(() => {});
  }
}

/**
 * 参数别名兜底：本地模型有时固执地用 Claude-Code 风格的参数名
 * （file_path / cmd / old_str…），schema 校验不过就会无限重试同一个调用
 * （2026-09-01 的 failed case：read 循环 140+ 次直到超时）。
 * prepareArguments 在框架的参数校验之前运行，把别名映射回正式参数名。
 */
const ARG_ALIASES: Record<string, string[]> = {
  path: ["file_path", "filePath", "filepath", "file", "filename"],
  command: ["cmd", "script"],
  content: ["text", "new_content", "newContent"],
  old_string: ["oldString", "old_str", "old", "oldText"],
  new_string: ["newString", "new_str", "new", "newText"],
};

function withArgAliases(tool: AgentTool<any>): AgentTool<any> {
  return {
    ...tool,
    prepareArguments: (args: unknown) => {
      const a =
        args && typeof args === "object" && !Array.isArray(args)
          ? { ...(args as Record<string, unknown>) }
          : {};
      const props =
        (tool.parameters as { properties?: Record<string, unknown> })
          ?.properties ?? {};
      for (const key of Object.keys(props)) {
        if (a[key] === undefined) {
          for (const alias of ARG_ALIASES[key] ?? []) {
            if (a[alias] !== undefined) {
              a[key] = a[alias];
              delete a[alias];
              break;
            }
          }
        }
      }
      return tool.prepareArguments ? tool.prepareArguments(a) : a;
    },
  };
}

export function createTools(cwd: string = resolveWorkspace()): AgentTool<any>[] {
  const atomicOperations = {
    writeFile: atomicWriteFile,
  };
  return [
    ...(createCodingTools(cwd, {
      write: {
        operations: {
          ...atomicOperations,
          mkdir: (dir) => mkdir(dir, { recursive: true }).then(() => {}),
        },
      },
      edit: {
        operations: {
          ...atomicOperations,
          readFile,
          access: (target) => access(target),
        },
      },
    }) as AgentTool<any>[]).map(withArgAliases),
    echoTool,
    // TODO: 在这里加入你的自定义工具
  ];
}
