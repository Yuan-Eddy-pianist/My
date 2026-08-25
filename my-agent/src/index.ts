/**
 * CLI 入口：一个简单的交互式 REPL。
 *
 *   npm run dev            # 交互模式（需先接入 LLM）
 *   npm run dev -- "你好"   # 单次提问
 */
import * as readline from "node:readline/promises";
import { createAgent } from "./agent.js";

async function main() {
  const oneShot = process.argv.slice(2).join(" ").trim();

  const agent = createAgent();

  // 订阅事件：流式输出文本 + 工具调用提示
  agent.subscribe((event: any) => {
    if (
      event.type === "message_update" &&
      event.assistantMessageEvent?.type === "text_delta"
    ) {
      process.stdout.write(event.assistantMessageEvent.delta);
    } else if (event.type === "tool_execution_start") {
      process.stdout.write(`\n[tool] ${event.toolName ?? event.name ?? "?"}\n`);
    } else if (event.type === "message_end") {
      process.stdout.write("\n");
    }
  });

  if (oneShot) {
    await agent.prompt(oneShot);
    return;
  }

  console.log("my-agent · 输入消息开始对话，Ctrl+C 退出\n");
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  while (true) {
    const line = (await rl.question("you: ")).trim();
    if (!line) continue;
    if (line === "/exit" || line === "/quit") break;
    try {
      process.stdout.write("agent: ");
      await agent.prompt(line);
    } catch (err) {
      console.error(`\n[error] ${err instanceof Error ? err.message : err}`);
    }
  }
  rl.close();
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
