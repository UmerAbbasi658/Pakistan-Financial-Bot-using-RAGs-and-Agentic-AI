import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"  

def query_groq_with_context(question, context):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a financial assistant strictly limited to Pakistani stock market or economy."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ]
    }
    response = requests.post(GROQ_URL, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]