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
    
    # Show the prompt that will be sent to the LLM
    from app.services.prompt_templates import PromptTemplates
    
    # Extract file texts if files are provided
    extracted_file_texts = []
    if uploaded_files:
        for file_content in uploaded_files:
            # Reset file pointer and extract text
            file_content.seek(0)
            text = svc._extract_text_from_bytes(file_content.read())
            extracted_file_texts.append(text)
            file_content.seek(0)  # Reset for actual processing
    
    # Check if context is completely empty - matches service logic
    context_is_empty = (
        not request.current_context.device_constants and 
        not request.current_context.information.strip()
    )
    
    # Build and display the actual prompt that will be sent
    if extracted_file_texts:
        # Template B: For messages with files (always prioritize file processing)
        prompt = PromptTemplates.build_template_b_prompt(
            context=request.current_context,
            stage=request.current_stage,
            user_message=request.message,
            mcq_responses=request.mcq_responses,
            extracted_file_texts=extracted_file_texts,
            previous_copilot_message=request.previous_copilot_message
        )
        print("\n[Backend -> LLM] Template B prompt (with files):\n")
    elif context_is_empty and request.current_stage.value == "gathering_requirements":
        # Empty context prompt: For completely new projects - optimized for off-topic detection
        prompt = PromptTemplates.build_empty_context_prompt(
            user_message=request.message,
            mcq_responses=request.mcq_responses,
            previous_copilot_message=request.previous_copilot_message
        )
        print("\n[Backend -> LLM] Empty Context prompt (off-topic detection optimized):\n")
    else:
        # Template A: For messages without files
        prompt = PromptTemplates.build_template_a_prompt(
            context=request.current_context,
            stage=request.current_stage,
            user_message=request.message,
            mcq_responses=request.mcq_responses,
            previous_copilot_message=request.previous_copilot_message
        )
        print("\n[Backend -> LLM] Template A prompt (no files):\n")
    
    print(prompt)
    print("\n" + "="*80)
    
    print("\n[Backend] Calling process_context_update (this will call the LLM with the above prompt)...\n")
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
    
    # Check if context is completely empty - matches service logic
    context_is_empty = (
        not request.current_context.device_constants and 
        not request.current_context.information.strip()
    )
    
    # Choose appropriate template and build prompt
    if extracted_file_texts:
        # Template B: For messages with files (always prioritize file processing)
        prompt = PromptTemplates.build_template_b_prompt(
            context=request.current_context,
            stage=request.current_stage,
            user_message=request.message,
            mcq_responses=request.mcq_responses,
            extracted_file_texts=extracted_file_texts
        )
        print("\n[Backend -> LLM] Template B prompt (with files):\n")
    elif context_is_empty and request.current_stage.value == "gathering_requirements":
        # Empty context prompt: For completely new projects - optimized for off-topic detection
        prompt = PromptTemplates.build_empty_context_prompt(
            user_message=request.message,
            mcq_responses=request.mcq_responses,
            previous_copilot_message=request.previous_copilot_message
        )
        print("\n[Backend -> LLM] Empty Context prompt (off-topic detection optimized):\n")
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
    print("Type 'exit' to quit, 'reset' to start over with empty context.")
    print("💡 Example automation projects to test:")
    print("  - Conveyor belt control with safety stops")
    print("  - Temperature monitoring and control system")
    print("  - Motor control with VFD")
    print("  - Packaging line automation")
    print("  - Water treatment plant control")
    print("\n⚡ Quick shortcuts:")
    print("  - 'quick:conveyor' - Start conveyor belt project")
    print("  - 'quick:temp' - Start temperature control project") 
    print("  - 'quick:motor' - Start motor control project")
    print("\n🎯 Goal: Build up requirements until progress reaches 100% and transitions to code generation\n")

    current_context = ProjectContext()
    current_stage = Stage.GATHERING_REQUIREMENTS
    previous_copilot_message = None

    while True:
        print("\n=== New Interaction ===")
        print(f"Current stage: {current_stage.value}")
        print(f"Current context summary:")
        print(f"  - Device constants: {len(current_context.device_constants)} devices")
        print(f"  - Information length: {len(current_context.information)} chars")
        if current_context.information:
            print(f"  - Information preview: {current_context.information[:200]!r}...")

        message = input("\nFrontend: Enter message (or ENTER for minimal update, 'exit' to quit, 'reset' to restart): ")
        
        if message.strip().lower() == "exit":
            print("Exiting interactive demo.")
            break
        elif message.strip().lower() == "reset":
            print("Resetting context to empty state...")
            current_context = ProjectContext()
            current_stage = Stage.GATHERING_REQUIREMENTS
            previous_copilot_message = None
            continue
        elif message.strip().lower().startswith("quick:"):
            # Quick test scenarios
            scenario = message.strip()[6:].strip()
            if scenario == "conveyor":
                message = "I want to control a conveyor belt system with safety stops and speed control"
            elif scenario == "temp":
                message = "I need a temperature monitoring and control system for a heating process"
            elif scenario == "motor":
                message = "I want to control a motor with VFD and safety interlocks"
            else:
                print(f"Unknown quick scenario: {scenario}")
                continue

        # Handle MCQ responses
        mcq_responses = []
        mcq_input = input("Frontend: MCQ responses (comma-separated, or ENTER for none): ")
        if mcq_input.strip():
            mcq_responses = [r.strip() for r in mcq_input.split(",")]

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
            mcq_responses=mcq_responses,
            current_context=current_context,
            current_stage=current_stage,
            previous_copilot_message=previous_copilot_message
        )

        print("\n[Frontend -> Backend] POST /api/v1/context/update payload:\n")
        print(pretty(req.model_dump()))

        # Show prompts and optionally run live
        if live:
            try:
                resp = await run_live_flow(req, uploaded_files=uploaded_files)
                
                # Update local context with response
                current_context = ProjectContext(**resp.updated_context.model_dump())
                current_stage = resp.current_stage
                previous_copilot_message = resp.chat_message
                
                # Show progress information
                if resp.gathering_requirements_estimated_progress is not None:
                    progress_pct = int(resp.gathering_requirements_estimated_progress * 100)
                    print(f"\n[Progress] Requirements gathering: {progress_pct}% complete")
                    if resp.gathering_requirements_estimated_progress >= 1.0:
                        print("🎉 Requirements gathering complete! Ready for code generation.")
                        print("💡 Tip: Set stage to 'code_generation' in next interaction to generate code.")
                
                # Show MCQ information if present
                if resp.is_mcq:
                    print(f"\n[MCQ] Question: {resp.mcq_question}")
                    print(f"[MCQ] Options: {resp.mcq_options}")
                    print(f"[MCQ] Multi-select: {resp.is_multiselect}")
                
                # Show generated code if present
                if resp.generated_code:
                    print(f"\n[Code Generated] {len(resp.generated_code)} characters of Structured Text")
                    print(f"Preview: {resp.generated_code[:200]}...")
                
            except Exception as e:
                print(f"Error during live flow: {e}")
        else:
            simulated = run_dry_flow(req, uploaded_files=uploaded_files)
            # Don't mutate context in dry-run

        cont = input("\nContinue with another interaction? (y/n) ")
        if cont.strip().lower() not in ("y", "yes"):
            break

    # Final context summary
    print("\n=== Final Context Summary ===")
    print(f"Stage: {current_stage.value}")
    print(f"Device constants: {len(current_context.device_constants)} devices")
    if current_context.device_constants:
        for name, device in current_context.device_constants.items():
            print(f"  - {name}: {type(device).__name__ if hasattr(device, '__class__') else 'dict'}")
    print(f"Information: {len(current_context.information)} characters")
    if current_context.information:
        print(f"Preview:\n{current_context.information[:500]}...")
    
    print("\nInteractive demo finished.")


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
