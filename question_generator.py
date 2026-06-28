import google.generativeai as genai
import json
import os
import random

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

GK_TOPICS = [
    "World Geography", "Indian History", "Science & Technology",
    "Sports", "Famous Personalities", "Current Affairs",
    "Space & Universe", "Animals & Nature", "Art & Culture",
    "Economics & Finance", "World History", "Politics"
]

def generate_question():
    topic = random.choice(GK_TOPICS)

    prompt = f"""Generate a General Knowledge MCQ question about {topic}.
Return ONLY a JSON object in this exact format, no extra text:
{{
  "question": "Your question here?",
  "options": {{
    "A": "First option",
    "B": "Second option",
    "C": "Third option",
    "D": "Fourth option"
  }},
  "answer": "A",
  "explanation": "Brief explanation why this is correct.",
  "topic": "{topic}"
}}
Make sure the question is interesting, factual, and the answer is accurate."""

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Clean up markdown if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    return data

if __name__ == "__main__":
    q = generate_question()
    print(json.dumps(q, indent=2))
