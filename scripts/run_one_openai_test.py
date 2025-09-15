#!/usr/bin/env python3
"""One-off runner to call OpenAIService.chat_completion and print parsed + raw responses.

Usage:
  PYTHONPATH=/home/jonas-petersen/dev/plc-copilot OPENAI_API_KEY=... python scripts/run_one_openai_test.py
"""
import os
import sys
import json
import asyncio

from app.services.openai_service import OpenAIService
from app.core.config import settings


def main():
    key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
    if not key:
        print("OPENAI_API_KEY not set in environment or settings (.env). Exiting.")
        sys.exit(2)

    svc = OpenAIService()

    class Req:
        user_prompt = "Hello from test - please respond with the model name"
        model = "gpt-5-nano"
        # Use default model-friendly temperature to avoid unsupported_value errors
        temperature = 1.0
        max_tokens = 64
        max_completion_tokens = 64

    try:
        content, usage = asyncio.get_event_loop().run_until_complete(svc.chat_completion(Req()))

        print("--- PARSED CONTENT ---")
        print(repr(content))
        print("--- USAGE ---")
        print(usage)

        # Raw client call for full shape
        messages = [{"role": "user", "content": Req.user_prompt}]
        raw_kwargs = {
            "model": Req.model,
            "messages": messages,
            "temperature": Req.temperature,
            "max_completion_tokens": Req.max_completion_tokens,
        }

        print("--- OUTGOING RAW KWARGS ---")
        try:
            print(json.dumps(raw_kwargs, indent=2))
        except Exception:
            print(repr(raw_kwargs))

        raw_resp = svc.client.chat.completions.create(**raw_kwargs)

        print("--- RAW RESP REPR ---")
        print(repr(raw_resp))

        print("--- RAW RESP AS JSON/DICT (best-effort) ---")
        parsed_raw = None
        try:
            parsed_raw = raw_resp.to_dict()
            print(json.dumps(parsed_raw, indent=2, default=str))
        except Exception:
            try:
                parsed_raw = raw_resp.json()
                print(json.dumps(parsed_raw, indent=2, default=str))
            except Exception:
                print("(failed to serialize raw response)")

        # If the model stopped because of length and produced no visible content,
        # retry with a larger max_completion_tokens to confirm whether increasing
        # the limit yields visible output.
        try:
            if parsed_raw:
                choices = parsed_raw.get("choices", [])
                if choices:
                    ch0 = choices[0]
                    finish = ch0.get("finish_reason")
                    msg = ch0.get("message") or {}
                    content_str = None
                    if isinstance(msg, dict):
                        content_str = msg.get("content")

                    if finish == "length" and (not content_str):
                        print("--- Detected finish_reason='length' with empty content. Retrying with larger max_completion_tokens=512 ---")
                        raw_kwargs2 = dict(raw_kwargs)
                        raw_kwargs2["max_completion_tokens"] = 512
                        try:
                            resp2 = svc.client.chat.completions.create(**raw_kwargs2)
                            print("--- Retry Raw resp repr ---")
                            print(repr(resp2))
                            try:
                                r2 = resp2.to_dict()
                                print(json.dumps(r2, indent=2, default=str))
                            except Exception:
                                try:
                                    r2 = resp2.json()
                                    print(json.dumps(r2, indent=2, default=str))
                                except Exception:
                                    print("(failed to serialize retry response)")
                        except Exception as e:
                            print("Retry failed:", e)
        except Exception:
            pass

    except Exception as e:
        print("Error calling OpenAI service:", e)
        sys.exit(1)


if __name__ == '__main__':
    main()
