from prompts import SYSTEM_PROMPT
import json
import openai
import os 
# from gpt4all import GPT4All

# model = GPT4All(
#     "mistral-7b-instruct-v0.1.Q4_0.gguf",
#     model_path="models",
#     device="cpu"
# )
# with model.chat_session():
#     response = model.generate(
#         "You are a dental receptionist AI. Say hello.",
#         max_tokens=60,
#         temp=0.2
#     )
#     print(response)





def run_llm(user_text: str) -> dict:
    """
    Takes raw user text and returns structured data in JSON according to SYSTEM_PROMPT.
    """
    try:
        from openai import OpenAI
        AVALAI_API_KEY = os.getenv("AVALAI_API_KEY")
        client = OpenAI(
            api_key=f"{AVALAI_API_KEY}",
            base_url="https://api.avalai.ir/v1",  # آدرس پایه
        )
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ]
        )
        raw_output = completion.choices[0].message.content.strip()

        # parse JSON safely
        structured_data = json.loads(raw_output)
        return structured_data

    except json.JSONDecodeError:
        # اگر JSON معتبر نبود، برگرداندن یک خطا
        return {
            "chief_complaint": None,
            "pain_level": None,
            "insurance_provider": None,
            "preferred_slot": None,
            "urgency": "low",
            "escalation_required": False,
            "escalation_reason": "invalid JSON from LLM"
        }






# def run_llm(user_text: str) -> dict:
#     """
#     Takes raw user text and returns structured data in JSON according to SYSTEM_PROMPT.
#     """
#     try:
#         messages = [
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": user_text}
#         ]

#         response = openai.chat.completions.create(
#             model="gpt-4o",
#             messages=messages,
#             temperature=0,
#         )

#         raw_output = response.choices[0].message.content.strip()

#         # parse JSON safely
#         structured_data = json.loads(raw_output)
#         return structured_data

#     except json.JSONDecodeError:
#         # اگر JSON معتبر نبود، برگرداندن یک خطا
#         return {
#             "chief_complaint": None,
#             "pain_level": None,
#             "insurance_provider": None,
#             "preferred_slot": None,
#             "urgency": "low",
#             "escalation_required": False,
#             "escalation_reason": "invalid JSON from LLM"
#         }





# import requests
# import json

# OPENROUTER_API_KEY = "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"
# MODEL = "google/gemini-2.0-flash-exp:free"  # یک نمونه مدل رایگان

# def run_llm(user_text: str) -> dict:
    
#     headers = {
#         "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": MODEL,
#         "messages": [
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": user_text}
#         ],
#         "temperature": 0
#     }

#     try:
#         res = requests.post(
#             "https://openrouter.ai/api/v1/chat/completions",
#             headers=headers,
#             json=payload,
#         )
#         res.raise_for_status()
#         raw_output = res.json()["choices"][0]["message"]["content"]
#         return json.loads(raw_output)
#     except Exception as e:
#         return {
#             "chief_complaint": None,
#             "pain_level": None,
#             "insurance_provider": None,
#             "preferred_slot": None,
#             "urgency": "low",
#             "escalation_required": False,
#             "escalation_reason": str(e)
#         }











# from huggingface_hub import InferenceClient
# import os

# HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
# client = InferenceClient(HF_API_KEY)

# def run_llm(prompt: str) -> dict:
#     HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")  # باید ست باشه
# client = InferenceClient(HF_API_KEY)

# def run_llm(prompt: str) -> dict:
#     model_id = "google/flan-t5-small"  # سبک و رایگان برای تست
#     try:
#         output = client.text_generation(model=model_id, inputs=prompt, max_new_tokens=150)
#         # بعضی خروجی‌ها لیست هستن، بعضی تک دیکشنری
#         text = output[0].generated_text if isinstance(output, list) else output.generated_text
#         return {"raw_text": text}
#     except Exception as e:
#         print("❌ LLM error:", e)
#         return {"raw_text": f"Error: {e}"}