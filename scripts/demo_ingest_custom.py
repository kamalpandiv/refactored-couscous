"""
demo_ingest_custom.py
─────────────────────────────────────────────────────────────────────────────
Demonstrates the /ingest/custom  ➜  /query  pipeline.

Story: A SaaS startup wants to seed a customer-support bot with hand-crafted
FAQ snippets. They POST raw strings, then simulate a support chat session to
verify the bot answers correctly from that custom knowledge.
─────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import time

import httpx

BASE_URL = "http://localhost:8000/api/v1"
INGEST_CUSTOM_ENDPOINT = f"{BASE_URL}/ingest/custom"
QUERY_ENDPOINT = f"{BASE_URL}/query"

# ── Hand-crafted product FAQ snippets ────────────────────────────────────────
FAQ_SNIPPETS = [
    # Billing
    "Our pricing plans are Starter ($9/mo), Growth ($29/mo), and Enterprise "
    "(custom). All plans include a 14-day free trial with no credit card required.",
    "To cancel your subscription, go to Settings → Billing → Cancel Plan. "
    "Your data is retained for 30 days after cancellation in case you change your mind.",
    "We accept Visa, MasterCard, American Express, and PayPal. "
    "Annual plans receive a 20% discount compared to monthly billing.",
    # Onboarding
    "After signing up, complete the 5-step onboarding wizard that guides you "
    "through connecting your data sources, inviting team members, and setting "
    "notification preferences.",
    "Team members can be invited from Settings → Team → Invite. "
    "They receive an email with a magic link valid for 48 hours. "
    "Admins can assign roles: Owner, Editor, or Viewer.",
    # Technical / Integrations
    "We integrate natively with Slack, Notion, Google Drive, GitHub, and Zapier. "
    "Custom webhooks are available on Growth and Enterprise plans.",
    "Our REST API follows OpenAPI 3.1 spec. API keys are scoped per project and "
    "can be rotated from Settings → API Keys. Rate limit is 1 000 req/min on Growth.",
    "Data is encrypted at rest (AES-256) and in transit (TLS 1.3). "
    "We are SOC 2 Type II certified and GDPR compliant. "
    "EU customers can opt into data residency within the Frankfurt AWS region.",
    # Support
    "Support hours are Monday–Friday 09:00–18:00 UTC. "
    "Enterprise customers get 24/7 dedicated Slack support. "
    "Average first-response time is under 2 hours.",
    "Our public status page is at status.acme.io. "
    "Subscribe to incident alerts via email or RSS feed.",
]

# ── Simulated support chat ───────────────────────────────────────────────────
SUPPORT_QUESTIONS = [
    "How much does the Growth plan cost per month?",
    "Can I cancel anytime and will I lose my data immediately?",
    "Does your platform integrate with Slack?",
    "What encryption do you use for stored data?",
    "I want to add a colleague — how do I invite them?",
    "What are your API rate limits?",
]


async def ingest_custom(texts: list[str]) -> dict:
    """POST /ingest/custom  — send raw text snippets."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            INGEST_CUSTOM_ENDPOINT,
            json={"texts": texts},
        )
    response.raise_for_status()
    return response.json()


async def ask(question: str) -> dict:
    """POST /query  — no file filter; search the whole knowledge base."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            QUERY_ENDPOINT,
            json={
                "message": question,
                "file_name": None,
                "translation_strategy": None,
            },
        )
    response.raise_for_status()
    return response.json()


async def main() -> None:
    print("=" * 70)
    print("  DEMO: Ingest Custom Text  →  Support-Bot Chat Simulation")
    print("=" * 70)

    # ── Step 1: seed knowledge base ──────────────────────────────────────────
    print(f"\n[1] Ingesting {len(FAQ_SNIPPETS)} FAQ snippets …\n")
    result = await ingest_custom(FAQ_SNIPPETS)
    print(f"    status : {result.get('status')}")
    print(f"    count  : {result.get('count')} snippets stored synchronously")

    # ingest/custom is synchronous (no BackgroundTasks), but give a moment
    time.sleep(2)

    # ── Step 2: simulate support chat ────────────────────────────────────────
    print("\n[2] Running simulated customer support session …\n")
    for i, question in enumerate(SUPPORT_QUESTIONS, 1):
        print(f"  👤 Customer: {question}")
        data = await ask(question)
        answer = data.get("answer", "(no answer returned)")
        print(f"  🤖 Bot     : {answer}\n")
        print("  " + "─" * 66 + "\n")

    print("[✓] Support session complete.")


if __name__ == "__main__":
    asyncio.run(main())
