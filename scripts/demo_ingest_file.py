"""
demo_ingest_file.py
─────────────────────────────────────────────────────────────────────────────
Demonstrates the /ingest/file  ➜  /query  pipeline.

Story: A paralegal uploads an NDA PDF to the knowledge base and then runs a
checklist of legal questions against it — surfacing risky clauses fast.
─────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import os
import time

import httpx

BASE_URL = "http://localhost:8000/api/v1"
INGEST_FILE_ENDPOINT = f"{BASE_URL}/ingest/file"
QUERY_ENDPOINT = f"{BASE_URL}/query"

# ── point this at any local PDF or TXT file ──────────────────────────────────
FILE_PATH = "sample_nda.pdf"  # adjust to a real file on your machine

NDA_CHECKLIST = [
    "What is the duration of the confidentiality obligation?",
    "Are there any carve-outs or exceptions to what counts as confidential?",
    "Which party bears the cost of litigation in a breach scenario?",
    "Is there a non-compete clause? If so, what are the restrictions?",
    "What governing law and jurisdiction does the agreement specify?",
]


async def ingest_file(path: str) -> dict:
    """POST /ingest/file  — upload a PDF or TXT file."""
    filename = os.path.basename(path)
    mime = "application/pdf" if filename.endswith(".pdf") else "text/plain"

    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(path, "rb") as fh:
            response = await client.post(
                INGEST_FILE_ENDPOINT,
                files={"file": (filename, fh, mime)},
            )
    response.raise_for_status()
    return response.json()


async def ask(question: str, filename: str, strategy: str = "hyde") -> dict:
    """POST /query  — ask a question scoped to the uploaded file."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            QUERY_ENDPOINT,
            json={
                "message": question,
                "file_name": filename,
                "translation_strategy": strategy,
            },
        )
    response.raise_for_status()
    return response.json()


async def main() -> None:
    print("=" * 70)
    print("  DEMO: Ingest File (PDF/TXT)  →  Legal Clause Checklist")
    print("=" * 70)

    if not os.path.exists(FILE_PATH):
        print(f"\n  ⚠  File not found: {FILE_PATH}")
        print("     Create a sample NDA PDF or update FILE_PATH and re-run.\n")
        return

    filename = os.path.basename(FILE_PATH)

    # ── Step 1: upload ───────────────────────────────────────────────────────
    print(f"\n[1] Uploading file: {filename}\n")
    result = await ingest_file(FILE_PATH)
    print(f"    filename : {result.get('filename')}")
    print(f"    status   : {result.get('status')}")

    print("\n    Waiting 6 s for background ingestion to complete …")
    time.sleep(6)

    # ── Step 2: run checklist ────────────────────────────────────────────────
    print("\n[2] Running NDA legal checklist …\n")
    for i, clause_question in enumerate(NDA_CHECKLIST, 1):
        print(f"  ✎ Clause {i}: {clause_question}")
        data = await ask(clause_question, filename, strategy="hyde")
        answer = data.get("answer", "(no answer returned)")
        print(f"  ➜  {answer}\n")
        print("  " + "─" * 66 + "\n")

    print("[✓] Checklist complete.")


if __name__ == "__main__":
    asyncio.run(main())
