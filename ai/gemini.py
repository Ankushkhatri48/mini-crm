import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Support both .env (local) and Streamlit Cloud secrets
try:
    import streamlit as st
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "")
except Exception:
    api_key = os.getenv("GROQ_API_KEY", "")

client = Groq(api_key=api_key)

# Best free Groq model for instruction-following tasks
MODEL = "llama-3.3-70b-versatile"


def _call_groq(prompt: str, max_tokens: int = 512) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def generate_segment_filters(natural_language: str) -> dict:
    prompt = f"""
You are a CRM filter generator. Convert the following natural language into structured JSON filters.

Input: "{natural_language}"

Return ONLY a valid JSON object with these possible keys:
- min_spend (float): minimum total spend
- max_spend (float): maximum total spend
- min_orders (int): minimum total orders
- max_orders (int): maximum total orders
- city (string): exact city name

Example output:
{{"min_spend": 5000, "min_orders": 3}}

Return only the JSON object. No explanation. No markdown. No backticks.
"""
    try:
        text = _call_groq(prompt, max_tokens=256)
        # Strip any accidental markdown fences
        text = text.strip().strip("```json").strip("```").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "AI returned invalid JSON. Try rephrasing your description."}
    except Exception as e:
        return {"error": str(e)}


def generate_campaign_message(prompt_text: str, channel: str) -> str:
    prompt = f"""
You are a marketing copywriter. Generate a {channel} marketing message based on this brief:

"{prompt_text}"

Requirements:
- Channel: {channel}
- Concise and compelling
- Friendly, professional tone
- Clear call to action
- For WhatsApp/SMS: keep under 160 characters
- For Email/RCS: can be longer

Return only the message text. No explanation. No subject line label. No markdown.
"""
    try:
        return _call_groq(prompt, max_tokens=300)
    except Exception as e:
        return f"Error generating message: {str(e)}"
