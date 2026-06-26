from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from google import genai

from .config import GENERATION_MODEL

load_dotenv()


def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Create a .env file and add your free Gemini API key."
        )
    return genai.Client(api_key=api_key)


def generate_text(prompt: str, system_instruction: Optional[str] = None) -> str:
    client = get_client()
    full_prompt = prompt if not system_instruction else f"{system_instruction}\n\n{prompt}"
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=full_prompt,
    )
    return getattr(response, "text", "") or "No response generated."
