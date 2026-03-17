"""
demo_ingest_url.py
─────────────────────────────────────────────────────────────────────────────
Demonstrates the /ingest/url  ➜  /query  pipeline.

Story: A researcher wants to pull a Wikipedia article about climate change
into the knowledge base and then ask domain-specific questions against it.
─────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import time

import httpx

BASE_URL = "http://localhost:8000/api/v1"
INGEST_URL_ENDPOINT = f"{BASE_URL}/ingest/url"
QUERY_ENDPOINT = f"{BASE_URL}/query"

# ── change this to any publicly accessible URL ──────────────────────────────
TARGET_URL = "https://en.wikipedia.org/wiki/Climate_change"

QUESTIONS = [
    "What are the primary human activities responsible for climate change?",
    "How does climate change affect sea levels and coastal communities?",
    "What international agreements exist to combat climate change?",
]


async def ingest_url(url: str) -> dict:
    """POST /ingest/url  — scrape and ingest a web page."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            INGEST_URL_ENDPOINT,
            json={"url": url},
        )
    response.raise_for_status()
    return response.json()


async def ask(question: str, source_url: str) -> dict:
    """POST /query — ask a question scoped to the ingested URL."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            QUERY_ENDPOINT,
            json={
                "message": question,
                # file_name doubles as a source filter — pass the URL as-is
                "file_name": source_url,
                "translation_strategy": "multi_query",  # broaden recall
            },
        )
    response.raise_for_status()
    return response.json()


async def main() -> None:
    print("=" * 70)
    print("  DEMO: Ingest URL  →  Query")
    print("=" * 70)

    # ── Step 1: ingest ───────────────────────────────────────────────────────
    print(f"\n[1] Ingesting URL:\n    {TARGET_URL}\n")
    result = await ingest_url(TARGET_URL)
    print(f"    Status : {result.get('status')}")
    print(f"    URL    : {result.get('url')}")

    # Give the background task a moment to finish chunking/embedding
    print("\n    Waiting 5 s for background ingestion to complete …")
    time.sleep(5)

    # ── Step 2: query ────────────────────────────────────────────────────────
    print("\n[2] Querying the ingested article …\n")
    for i, question in enumerate(QUESTIONS, 1):
        print(f"  Q{i}: {question}")
        answer_data = await ask(question, TARGET_URL)
        print(f"  A{i}: {answer_data.get('answer', '(no answer)')}\n")
        print("  " + "─" * 66 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
