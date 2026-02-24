import pdfplumber

from .base import PageStrategy


class TextStrategy(PageStrategy):
    """
    Logic: Layout-aware text extraction.
    Crucial for multi-column PDFs like academic papers to prevent
    words from mashing together or columns reading left-to-right across the page.
    """

    def parse(self, page: pdfplumber.page.Page) -> str:
        # extract_text with layout=True preserves visual spaces and columns much better
        text = page.extract_text(
            layout=True,
            x_tolerance=2,  # Tweak this if words are still mashing together (higher = more spaces)
            y_tolerance=3,
        )

        if not text:
            return ""

        # Clean up the output by removing excessive empty lines that layout=True might create
        cleaned_lines = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)

        return "\n".join(cleaned_lines)
