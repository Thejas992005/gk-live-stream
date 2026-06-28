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
    "Economics & Finance", "World History", "Politics",
    "Inventions & Discoveries", "Literature & Books", "Human Body & Biology"
]

DIFFICULTIES = ["Easy", "Medium", "Hard", "Tricky"]
ANGLES = [
    "Focus on an interesting or unique trivia fact.",
    "Ask about a specific historical event, year, or figure.",
    "Ask about a record holder, landmark, or scientific concept.",
    "Focus on a surprising detail or lesser-known fact."
]

FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free",
]

# Track seen questions in memory to prevent repetitions
SEEN_QUESTIONS = set()
MAX_SEEN_HISTORY = 300

def generate_question(retries=5):
    global SEEN_QUESTIONS
    
    for attempt_all in range(retries):
        topic = random.choice(GK_TOPICS)
        difficulty = random.choice(DIFFICULTIES)
        angle = random.choice(ANGLES)
        random_seed = random.randint(1000, 9999)
        
        prompt = f"""Generate a unique {difficulty} General Knowledge MCQ question about {topic}.
Guidance: {angle}
Avoid standard cliches (e.g. do NOT ask 'capital of France' or 'largest planet').
Seed ID: {random_seed}

Return ONLY a JSON object in this exact format, with no extra text or markdown code blocks:
{{
  "question": "Your unique question here?",
  "options": {{"A": "First option","B": "Second option","C": "Third option","D": "Fourth option"}},
  "answer": "A",
  "explanation": "Brief explanation why this is correct.",
  "topic": "{topic}"
}}"""

        for model in FREE_MODELS:
            print(f"Trying model: {model} (Attempt {attempt_all+1})")
            for attempt in range(2):
                try:
                    time.sleep(1)
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
                            "temperature": 0.85,
                            "max_tokens": 500
                        },
                        timeout=15
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
                    
                    q_text = result.get("question", "").strip().lower()
                    if not q_text or q_text in SEEN_QUESTIONS:
                        print(f"⚠️ Duplicate question detected ({q_text[:30]}...). Retrying...")
                        continue
                    
                    # Store in seen questions history
                    SEEN_QUESTIONS.add(q_text)
                    if len(SEEN_QUESTIONS) > MAX_SEEN_HISTORY:
                        SEEN_QUESTIONS = set(list(SEEN_QUESTIONS)[-150:])

                    print(f"✅ Unique Question generated using {model}")
                    return result
                except Exception as e:
                    print(f"Attempt {attempt+1} with {model} failed: {e}")
                    time.sleep(3)

    raise Exception("Failed to generate a unique question after multiple retries.")

if __name__ == "__main__":
    q = generate_question()
    print(json.dumps(q, indent=2))
