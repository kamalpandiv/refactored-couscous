import io

import pdfplumber
from fastapi import UploadFile

from app.components.loaders.strategies.router import PDFPageRouter


async def parse_pdf(file: UploadFile) -> str:
    """
    Parses a PDF file by analyzing each page individually and applying
    the best strategy (Text, Table, or OCR).
    """
    content = await file.read()
    pdf_stream = io.BytesIO(content)

    router = PDFPageRouter()
    full_text = []

    # Open the PDF once
    with pdfplumber.open(pdf_stream) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing PDF: {file.filename} ({total_pages} pages)")

        for i, page in enumerate(pdf.pages):
            # 1. Decide Strategy for THIS page
            strategy = router.get_strategy(page)

            # 2. Parse
            page_content = strategy.parse(page)

            # 3. Add to result with metadata (Optional: Page numbers help LLMs)
            header = f"--- Page {i + 1} ---\n"
            full_text.append(header + page_content)

    return "\n\n".join(full_text)
