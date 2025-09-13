import { OpenAI } from "openai";

const client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});


// Example of user message
const userMessageExample = "My back pain is at a 7, I have Sun Life insurance, and I’d like to book on September 7th at 3:30 PM.";

// Example of making an agent to fill out a form with the user's input with a naive single shot approach
await client.chat.completions.create({
    model: "gpt-5",
    messages: [
        {
            role: "system",
            content: "You are a specialized agent that extracts patient booking details from user messages."
        },
        {
            role: "user",
            content: userMessageExample
        }
    ],
    tools: [
        {
            type: "function",
            function: {
                name: "extract_patient_info",
                description: "Extract patient booking details",
                parameters: {
                    type: "object",
                    properties: {
                        pain_level: { type: "string", description: "The pain level of the patient" },
                        insurance: { type: "string", description: "The insurance of the patient" },
                        preferred_slot: { type: "string", format: "date-time", description: "The preferred slot of the patient" }
                    },
                    required: ["pain_level", "insurance", "preferred_slot"]
                }
            }
        }
    ],
    tool_choice: "auto"
});

// I expect the output to be something like this:

export const expectedOutput = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1699999999,
    "model": "gpt-5",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "extract_patient_info",
                            "arguments": "{\n  \"pain_level\": \"7/10\",\n  \"insurance\": \"Sun Life\",\n  \"preferred_slot\": \"2025-09-07T15:30:00\"\n}"
                        }
                    }
                ]
            },
            "finish_reason": "tool_calls"
        }
    ],
    "usage": {
        "prompt_tokens": 60,
        "completion_tokens": 30,
        "total_tokens": 90
    }
};