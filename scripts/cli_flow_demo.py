#!/usr/bin/env python3
"""
Interactive CLI demo that walks the full flow:

frontend -> backend API
backend -> LLM (prints full prompt)
LLM -> backend answer
backend -> frontend (prints API response)

Usage:
  python scripts/cli_flow_demo.py [--live]

--live : actually call the backend which will call the LLM (requires OPENAI_API_KEY and network)
Without --live the script will only show the prompts and simulate the flow without calling OpenAI.
"""

import argparse
import asyncio
import json
from typing import Optional
from io import BytesIO

from app.services.context_service import ContextProcessingService
from app.services.openai_service import OpenAIService
from app.schemas.context import ProjectContext, ContextUpdateRequest, Stage


def pretty(obj):
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception:
        return str(obj)


async def run_live_flow(request: ContextUpdateRequest, uploaded_files=None):
    svc = ContextProcessingService()
    print("\n[Backend] Calling process_context_update (this will call the LLM internally)...\n")
    response = await svc.process_context_update(request, uploaded_files=uploaded_files)
    print("\n[Backend -> Frontend] Final API response (ContextUpdateResponse):\n")
    out = response.model_dump()
    # If file extractions present, ensure they're visible
    if out.get("file_extractions"):
        print("\n[Backend] File extractions:\n")
        print(pretty(out.get("file_extractions")))
    print(pretty(out))
    return response


def run_dry_flow(request: ContextUpdateRequest, uploaded_files=None):
    """Build and show prompts that would be sent to the LLM without calling it."""
    from app.services.prompt_templates import PromptTemplates
    from app.services.context_service import ContextProcessingService
    
    svc = ContextProcessingService()
    
    # Extract file texts if files are provided
    extracted_file_texts = []
    if uploaded_files:
        for file_content in uploaded_files:
            # Simulate file text extraction
            text = svc._extract_text_from_bytes(file_content.read())
            extracted_file_texts.append(text[:1000] + "...[truncated]" if len(text) > 1000 else text)
    
    # Choose appropriate template and build prompt
    if extracted_file_texts:
        # Template B: For messages with files
        prompt = PromptTemplates.build_template_b_prompt(
            context=request.current_context,
            stage=request.current_stage,
            user_message=request.message,
            mcq_responses=request.mcq_responses,
            extracted_file_texts=extracted_file_texts
        )
        print("\n[Backend -> LLM] Template B prompt (with files):\n")
    else:
        # Template A: For messages without files
        prompt = PromptTemplates.build_template_a_prompt(
            context=request.current_context,
            stage=request.current_stage,
            user_message=request.message,
            mcq_responses=request.mcq_responses
        )
        print("\n[Backend -> LLM] Template A prompt (no files):\n")
    
    print(prompt)

    # Simulate a canned backend response
    print("\n[Backend -> Frontend] Simulated API response (no LLM call):\n")
    simulated = {
        "updated_context": request.current_context.model_dump(),
        "chat_message": "(dry-run) This is a simulated AI response. To get real responses, run with --live.",
        "gathering_requirements_estimated_progress": 0.1 if request.current_stage == Stage.GATHERING_REQUIREMENTS else None,
        "current_stage": request.current_stage.value,
        "is_mcq": False,
        "is_multiselect": False,
        "mcq_question": None,
        "mcq_options": [],
        "generated_code": None,
        "file_extractions": [{"extracted_devices": {}, "extracted_information": "Simulated file extraction", "processing_summary": "Dry run - no actual file processing"}] if uploaded_files else []
    }
    # If an uploaded file was provided, simulate a file_extractions entry
    if uploaded_files:
        simulated["file_extractions"] = [{
            "extracted_devices": {},
            "extracted_information": "(dry-run) Simulated extraction from PDF",
            "processing_summary": "Simulated PDF extraction"
        }]
    print(pretty(simulated))
    return simulated


async def interactive_loop(live: bool):
    print("Interactive CLI demo: Frontend -> Backend -> LLM -> Backend -> Frontend")
    print("Type 'exit' to quit.\n")

    current_context = ProjectContext()
    current_stage = Stage.GATHERING_REQUIREMENTS

    while True:
        print("\n=== New Interaction ===")
        print(f"Current stage: {current_stage.value}")
        print(f"Current context (summary): {current_context.information[:200]!r}")

        message = input("Frontend: Enter message (or press ENTER to send minimal update): ")
        if message.strip().lower() == "exit":
            print("Exiting interactive demo.")
            break

        stage_in = input(f"Frontend: Desired stage [{current_stage.value}] (press ENTER to keep): ")
        if stage_in.strip():
            try:
                current_stage = Stage(stage_in.strip())
            except Exception:
                print("Invalid stage provided, using previous stage.")

        # Ask user whether to include the sample PDF
        use_pdf = input("Include sample PDF (uploads/KV-8000A_Datasheet.pdf)? (y/n) ")
        uploaded_files = None
        if use_pdf.strip().lower() in ("y", "yes"):
            pdf_path = "/home/jonas-petersen/dev/plc-copilot/uploads/KV-8000A_Datasheet.pdf"
            try:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                uploaded_files = [BytesIO(pdf_bytes)]
                print(f"Included PDF: {pdf_path} ({len(pdf_bytes)} bytes)")
            except Exception as e:
                print(f"Failed to read PDF {pdf_path}: {e}")

        req = ContextUpdateRequest(
            message=message or None,
            mcq_responses=[],
            current_context=current_context,
            current_stage=current_stage
        )

        print("\n[Frontend -> Backend] POST /api/v1/context/update payload:\n")
        print(pretty(req.model_dump()))

        # Show prompts and optionally run live
        if live:
            try:
                resp = await run_live_flow(req, uploaded_files=uploaded_files)
                # Update local context with response
                updated = resp.updated_context
                current_context = ProjectContext(**updated.model_dump())
                current_stage = resp.current_stage
            except Exception as e:
                print(f"Error during live flow: {e}")
        else:
            simulated = run_dry_flow(req, uploaded_files=uploaded_files)
            # don't mutate context in dry-run

        cont = input("Do another interaction? (y/n) ")
        if cont.strip().lower() not in ("y", "yes"):
            break

    print("Interactive demo finished.")


def main():
    parser = argparse.ArgumentParser(description="CLI demo for interactive LLM flow")
    parser.add_argument("--live", action="store_true", help="Call the backend/LLM for real (requires API key)")
    args = parser.parse_args()

    try:
        asyncio.run(interactive_loop(live=args.live))
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    main()
