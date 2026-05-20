// @ts-nocheck — AI SDK v6's ToolSet is a 4-way union (Tool<never,never> | Tool<any,any> | ...)
// that causes TypeScript's type checker to OOM when inferring GenerateTextResult<TOOLS>.
// Runtime correctness is guaranteed by Zod schemas on every tool input.
import { generateText, tool, stepCountIs, type ToolSet } from 'ai';
import { openai } from '@ai-sdk/openai';
import { ILanguageModel, ChatMessage, LLMTurnResult, ToolEvent } from '../../application/ports/ILanguageModel';
import {
  DENTAL_QUALIFIER_SYSTEM_PROMPT,
  DENTAL_TOOL_DESCRIPTIONS,
  DentalToolArgs,
  painInfoSchema,
  insuranceSchema,
  appointmentSchema,
  escalationSchema,
  endConversationSchema,
} from '../../prompts/dentalQualifier';

export class GPT4oLanguageModel implements ILanguageModel {
  async chat(history: ChatMessage[], userMessage: string): Promise<LLMTurnResult> {
    const toolEvents: ToolEvent[] = [];

    // Explicit ToolSet annotation prevents TypeScript from inferring deep per-tool
    // generics on generateText<TOOLS>, which causes OOM on complex AI SDK types.
    const tools: ToolSet = {
      collect_pain_info: tool({
        description: DENTAL_TOOL_DESCRIPTIONS.collect_pain_info,
        inputSchema: painInfoSchema,
        execute: async (args: DentalToolArgs['collect_pain_info']) => {
          toolEvents.push({ type: 'collect_pain_info', ...args });
          return { status: 'recorded' };
        },
      }),
      collect_insurance: tool({
        description: DENTAL_TOOL_DESCRIPTIONS.collect_insurance,
        inputSchema: insuranceSchema,
        execute: async (args: DentalToolArgs['collect_insurance']) => {
          toolEvents.push({ type: 'collect_insurance', ...args });
          return { status: 'recorded' };
        },
      }),
      collect_appointment_preference: tool({
        description: DENTAL_TOOL_DESCRIPTIONS.collect_appointment_preference,
        inputSchema: appointmentSchema,
        execute: async (args: DentalToolArgs['collect_appointment_preference']) => {
          toolEvents.push({ type: 'collect_appointment_preference', ...args });
          return { status: 'recorded' };
        },
      }),
      escalate_to_human: tool({
        description: DENTAL_TOOL_DESCRIPTIONS.escalate_to_human,
        inputSchema: escalationSchema,
        execute: async (args: DentalToolArgs['escalate_to_human']) => {
          toolEvents.push({ type: 'escalate_to_human', ...args });
          return { status: 'recorded' };
        },
      }),
      end_conversation: tool({
        description: DENTAL_TOOL_DESCRIPTIONS.end_conversation,
        inputSchema: endConversationSchema,
        execute: async (args: DentalToolArgs['end_conversation']) => {
          toolEvents.push({ type: 'end_conversation', outcome: args.outcome });
          return { status: 'recorded' };
        },
      }),
    };

    const result = await generateText({
      model: openai('gpt-4o'),
      system: DENTAL_QUALIFIER_SYSTEM_PROMPT,
      messages: history.map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      })),
      tools,
      stopWhen: stepCountIs(10),
    });

    return { reply: result.text, toolEvents };
  }
}
