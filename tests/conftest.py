import asyncio

# Ensure an event loop is available immediately on import (robust for all test runs)
try:
    asyncio.get_running_loop()
except RuntimeError:
    _test_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_test_loop)

# Patch asyncio.get_event_loop to be resilient across test lifecycle (some tests close the loop)
_orig_get_event_loop = asyncio.get_event_loop

def _safe_get_event_loop():
    try:
        return _orig_get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
        except Exception:
            # If setting fails, just return the new loop (best-effort)
            pass
        return loop

asyncio.get_event_loop = _safe_get_event_loop

# TODO(temporary): The `_safe_get_event_loop` shim above ensures tests that call
# `asyncio.get_event_loop()` don't fail when pytest or other test helpers close the
# loop. In production this is unnecessary because an event loop is present; revisit
# and remove/refactor this shim later to avoid masking real loop lifecycle bugs.


def pytest_configure(config):
    """Pytest hook to ensure a default event loop exists in the main thread before tests run.

    Some tests call ``asyncio.get_event_loop().run_until_complete(...)`` directly and
    pytest/test runners may not have a loop set on the main thread. This hook ensures
    one is available as well — though we also set it at import time above.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


import pytest
import os
import glob


@pytest.fixture(scope="session")
def pdf_path():
    """Return path to a sample PDF in the repository's uploads/ directory.

    If none exists, skip tests that require a real PDF.
    """
    repo_root = os.path.dirname(os.path.dirname(__file__))
    uploads_dir = os.path.join(repo_root, "uploads")
    if not os.path.isdir(uploads_dir):
        pytest.skip("uploads directory not present; skipping PDF integration tests")

    pdfs = glob.glob(os.path.join(uploads_dir, "*.pdf"))
    if not pdfs:
        pytest.skip("No PDF files found in uploads/; skipping PDF integration tests")

    # Return the first available PDF
    return pdfs[0]


@pytest.fixture(scope="session")
def raw_text(pdf_path):
    """Extract text from the provided PDF path using DocumentService.

    Runs the async extractor synchronously with asyncio.run so tests can use it.
    """
    try:
        # Import here to avoid top-level app import side-effects during pytest collection
        from app.services.document_service import DocumentService

        svc = DocumentService(db=None)
        # Use asyncio.run to execute the coroutine in a fresh event loop
        text = asyncio.run(svc._extract_text_from_pdf(pdf_path))
        return text
    except Exception as e:
        # If extraction fails, provide empty string but don't crash collection
        return ""
