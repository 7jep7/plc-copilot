"""Run a quick live smoke test calling OpenAI via OpenAIService.chat_completion.

This script expects the environment variable OPENAI_API_KEY to be set (or a .env file in the repo root).

Usage:
    conda activate plc-copilot
    python scripts/live_openai_smoke.py
"""
import os
import asyncio
import sys

from app.services.openai_service import OpenAIService
from app.core.config import settings


def main():
    # Prefer explicit environment variable but fall back to project settings
    key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
    if not key:
        print("OPENAI_API_KEY not found in environment or settings (.env). Set it and re-run.")
        sys.exit(2)

    svc = OpenAIService()

    class Req:
        user_prompt = "Say hello and report the model name"
        model = "gpt-5-nano"
        temperature = 0.2
        max_tokens = 64

    try:
        content, usage = asyncio.get_event_loop().run_until_complete(svc.chat_completion(Req()))
        print("--- Response ---")
        print(content)
        print("--- Usage ---")
        print(usage)
        sys.exit(0)
    except Exception as e:
        print("Live OpenAI call failed:", e)
        sys.exit(1)


if __name__ == '__main__':
    main()
