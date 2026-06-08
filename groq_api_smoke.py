# pip install openai
from __future__ import annotations

import sys
import os
from openai import OpenAI
from dotenv import load_dotenv

DEFAULT_PROMPT = "Привет! Ответь одним коротким предложением."
MODEL = "openai/gpt-oss-120b"


def build_client() -> OpenAI:
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY before running.")
    
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )    

def ask_model(client: OpenAI, prompt: str) -> str:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )

    return completion.choices[0].message.content or ""

def main() -> int:
    try:
        client = build_client()
        answer = ask_model(client, DEFAULT_PROMPT)
        print(answer)
        return 0
    except Exception as exc:
        print(f"Groq request failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
