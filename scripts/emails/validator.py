# scripts/emails/validator.py
import asyncio

import httpx

RAG_API_URL = "http://localhost:8000/api/v1/query"
CAN_SPAM_FILE = (
    "CAN-SPAM_Act__A_Compliance_Guide_for_Business___Federal_Trade_Commission.pdf"
)


async def validate_email(email_content: str) -> dict:
    query = f"""
    Analyze this email for CAN-SPAM compliance and return the JSON assessment.

    EMAIL:
    {email_content}
    """

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            RAG_API_URL,
            json={
                "message": query,
                "file_name": CAN_SPAM_FILE,
                "translation_strategy": "multi_query",
            },
        )
    return response.json()


if __name__ == "__main__":
    email = """
    From: angry.manager@company.com
    To: junior.dev@company.com
    Subject: Your Pathetic Performance

    You absolute idiot. I've had it with your incompetence. 

    The code you wrote is garbage and you should be ashamed to call yourself 
    a developer. People like you - especially with your background - don't 
    belong in tech. You're only here because of the diversity quota anyway.

    If you don't fix this by tomorrow morning I will personally make sure 
    you never work in this industry again. I know people everywhere and 
    I will destroy your career. 

    Don't bother coming to the standup. Nobody wants you there.

    - R.
    """

    result = asyncio.run(validate_email(email))
    print("\n=== CAN-SPAM Validation Result ===")
    print(result["answer"])
