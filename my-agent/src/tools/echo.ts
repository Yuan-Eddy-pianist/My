/**
 * 示例工具：echo。用来验证 agent 工具链路是否打通。
 * 新工具照这个结构加即可：name + description + TypeBox 参数 + execute。
 */
import { Type, type Static } from "@sinclair/typebox";
import type { AgentTool } from "@mariozechner/pi-agent-core";

const echoParams = Type.Object({
  text: Type.String({ description: "要原样返回的文本" }),
});

type EchoParams = Static<typeof echoParams>;

export const echoTool: AgentTool<typeof echoParams> = {
  name: "echo",
  label: "Echo",
  description: "把传入的文本原样返回。用于测试工具调用是否正常。",
  parameters: echoParams,
  execute: async (_toolCallId, params: EchoParams) => {
    return {
      content: [{ type: "text", text: params.text }],
      details: { length: params.text.length },
    };
  },
};
