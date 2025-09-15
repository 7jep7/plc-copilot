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
    import argparse

    parser = argparse.ArgumentParser(description="Live OpenAI smoke test (uses app OpenAIService)")
    parser.add_argument("--prompt", "-p", default="Say hello and report the model name", help="User prompt to send")
    parser.add_argument("--model", "-m", default="gpt-5-nano", help="Model to use")
    parser.add_argument("--temperature", "-t", type=float, default=1.0, help="Temperature to use")
    parser.add_argument("--max-tokens", type=int, default=None, help="Legacy max_tokens (will be mapped)")
    parser.add_argument("--max-completion-tokens", type=int, default=None, help="Preferred max_completion_tokens")
    parser.add_argument("--system", type=str, default=None, help="Optional system message to include")
    parser.add_argument("--raw", action="store_true", help="Also print raw client response and choices")
    args = parser.parse_args()

    # Prefer explicit environment variable but fall back to project settings
    key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
    if not key:
        print("OPENAI_API_KEY not found in environment or settings (.env). Set it and re-run.")
        sys.exit(2)

    svc = OpenAIService()

    # Build a lightweight request object compatible with the service API
    class Req:
        user_prompt = args.prompt
        model = args.model
        temperature = args.temperature
        # Keep legacy name to be compatible with existing code paths
        max_tokens = args.max_tokens or args.max_completion_tokens or 64
        max_completion_tokens = args.max_completion_tokens or args.max_tokens

    try:
        # First call the service helper (keeps compatibility with app flows)
        content, usage = asyncio.get_event_loop().run_until_complete(svc.chat_completion(Req()))
        print("--- Parsed Response (content) ---")
        print(repr(content))
        print("--- Usage ---")
        print(usage)

        if args.raw:
            # Also call the underlying client directly to show the raw response structure
            try:
                messages = []
                if args.system:
                    messages.append({"role": "system", "content": args.system})
                messages.append({"role": "user", "content": args.prompt})

                # Choose effective max_completion_tokens
                effective_max = args.max_completion_tokens if args.max_completion_tokens is not None else args.max_tokens

                raw_kwargs = dict(
                    model=args.model,
                    messages=messages,
                    temperature=args.temperature,
                )
                if effective_max is not None:
                    raw_kwargs["max_completion_tokens"] = effective_max
                # Log exactly what we're sending
                print("--- Outgoing raw kwargs sent to client ---")
                try:
                    import json

                    print(json.dumps(raw_kwargs, indent=2, default=str))
                except Exception:
                    print(repr(raw_kwargs))

                raw_resp = svc.client.chat.completions.create(**raw_kwargs)

                # Robustly print the incoming raw response
                print("--- Raw response object (repr) ---")
                print(repr(raw_resp))
                print("--- Raw response as dict/json (best-effort) ---")
                try:
                    # Some client responses support .to_dict()
                    d = raw_resp.to_dict()
                    import json

                    print(json.dumps(d, indent=2, default=str))
                except Exception:
                    try:
                        s = raw_resp.json()
                        import json

                        print(json.dumps(s, indent=2, default=str))
                    except Exception:
                        print("(failed to convert raw response to dict/json)")
                # Print choices if available
                try:
                    print("--- Raw choices ---")
                    for i, c in enumerate(getattr(raw_resp, 'choices', []) or []):
                        print(i, repr(getattr(c, 'message', getattr(c, 'text', c))))
                except Exception:
                    pass
            except Exception as e:
                print("Failed to fetch raw client response:", e)
        sys.exit(0)
    except Exception as e:
        print("Live OpenAI call failed:", e)
        sys.exit(1)


if __name__ == '__main__':
    main()
