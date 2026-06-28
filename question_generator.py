import requests
import json
import os
import random
import time

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

GK_TOPICS = [
    "World Geography", "Indian History", "Science & Technology",
    "Sports", "Famous Personalities", "Current Affairs",
    "Space & Universe", "Animals & Nature", "Art & Culture",
    "Economics & Finance", "World History", "Politics"
]

FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free",
]

def generate_question(retries=5):
    topic = random.choice(GK_TOPICS)
    prompt = f"""Generate a General Knowledge MCQ question about {topic}.
Return ONLY a JSON object in this exact format, no extra text, no markdown backticks:
{{
  "question": "Your question here?",
  "options": {{"A": "First option","B": "Second option","C": "Third option","D": "Fourth option"}},
  "answer": "A",
  "explanation": "Brief explanation why this is correct.",
  "topic": "{topic}"
}}"""

    for model in FREE_MODELS:
        print(f"Trying model: {model}")
        for attempt in range(3):
            try:
                time.sleep(2)
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://gk-livestream.railway.app",
                        "X-Title": "GK Live Stream Bot"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                if response.status_code == 404:
                    print(f"Model {model} not available, trying next...")
                    break
                if response.status_code != 200:
                    raise Exception(f"API error {response.status_code}: {response.text}")
                data = response.json()
                text = data["choices"][0]["message"]["content"].strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end > start:
                    text = text[start:end]
                result = json.loads(text)
                print(f"✅ Question generated using {model}")
                return result
            except Exception as e:
                print(f"Attempt {attempt+1} with {model} failed: {e}")
                time.sleep(10)

    raise Exception("All models failed")

if __name__ == "__main__":
    q = generate_question()
    print(json.dumps(q, indent=2))
