import pdfplumber
import requests
import tempfile
import os

def extract_pdf(url: str) -> dict:
    """
    Download a PDF from a URL and extract its text and tables.
    """
    tmp_path = None
    try:
        # Download the PDF
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        pages_text = []
        all_tables = []

        with pdfplumber.open(tmp_path) as pdf:
            total_pages = len(pdf.pages)

            for i, page in enumerate(pdf.pages[:20]):  # limit to 20 pages
                # Extract text
                text = page.extract_text()
                if text:
                    pages_text.append({
                        "page": i + 1,
                        "text": text.strip()
                    })

                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        # Convert to list of dicts
                        headers = table[0]
                        rows = []
                        for row in table[1:]:
                            if any(cell for cell in row):
                                rows.append(dict(zip(headers, row)))
                        if rows:
                            all_tables.append({
                                "page": i + 1,
                                "headers": headers,
                                "rows": rows
                            })

        full_text = "\n\n".join([p["text"] for p in pages_text])

        return {
            "total_pages": total_pages,
            "pages_extracted": len(pages_text),
            "full_text": full_text[:5000],
            "pages": pages_text,
            "tables": all_tables,
            "table_count": len(all_tables)
        }

    except Exception as e:
        return {
            "error": str(e),
            "total_pages": 0,
            "full_text": "",
            "tables": []
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)