import requests
from bs4 import BeautifulSoup


def parse_url(url: str) -> str:
    """
    Fetches a URL and returns the text content.
    Includes headers to mimic a real browser to avoid 403 errors.
    """
    try:
        # UPDATED: Headers to look like a standard Chrome browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script, style, and other non-content elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace (remove empty lines and extra spaces)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)

        return clean_text

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""
