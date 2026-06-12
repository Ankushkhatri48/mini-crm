import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Support both .env (local) and Streamlit Cloud secrets
try:
    import streamlit as st
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")
except Exception:
    api_key = os.getenv("GEMINI_API_KEY", "")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")


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

Return only the JSON, no explanation, no markdown.
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().strip("```json").strip("```").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}


def generate_campaign_message(prompt_text: str, channel: str) -> str:
    prompt = f"""
You are a marketing copywriter. Generate a {channel} marketing message based on this brief:

"{prompt_text}"

Requirements:
- Channel: {channel}
- Keep it concise and compelling
- Use a friendly, professional tone
- Include a clear call to action
- For WhatsApp/SMS: keep under 160 characters
- For Email/RCS: can be longer

Return only the message text, no explanation.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating message: {str(e)}"
