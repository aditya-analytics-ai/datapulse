import pandas as pd
import json
import io
from typing import Any
def extract_rows_from_cleaned(cleaned_data: dict) -> list:
    page_type = cleaned_data.get("page_type", "")

    if page_type == "table":
        tables = cleaned_data.get("tables", [])
        if not tables:
            return []
        # Pick the table with the most rows
        best_table = max(tables, key=lambda t: len(t.get("rows", [])))
        return best_table.get("rows", [])

    elif page_type == "article":
        data = cleaned_data.get("data", {})
        rows = []
        if data.get("paragraphs"):
            for i, p in enumerate(data["paragraphs"]):
                rows.append({"index": i + 1, "paragraph": p})
        return rows

    elif page_type == "json":
        data = cleaned_data.get("data", {})
        if isinstance(data.get("data"), list):
            return data["data"]
        return []

    elif page_type == "pdf":
        data = cleaned_data.get("data", {})
        tables = data.get("tables", [])
        if tables:
            best_table = max(tables, key=lambda t: len(t.get("rows", [])))
            return best_table.get("rows", [])
        pages = data.get("pages", [])
        return [{"page": p["page"], "text": p["text"]} for p in pages]

    elif page_type in ("amazon_products", "flipkart_products", "products"):
        return cleaned_data.get("products", [])

    elif page_type == "linkedin_jobs":
        return cleaned_data.get("jobs", [])

    elif page_type == "jsonld":
        return cleaned_data.get("items", [])

    return []


def to_csv(cleaned_data: dict) -> bytes:
    """Export cleaned data to CSV bytes."""
    rows = extract_rows_from_cleaned(cleaned_data)
    if not rows:
        return b"No data available"
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")


def to_excel(cleaned_data: dict) -> bytes:
    """Export cleaned data to Excel bytes."""
    rows = extract_rows_from_cleaned(cleaned_data)
    if not rows:
        df = pd.DataFrame([{"message": "No data available"}])
    else:
        df = pd.DataFrame(rows)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="ScrapedData")

        # Auto-size columns
        worksheet = writer.sheets["ScrapedData"]
        for col in worksheet.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception:
                    pass
            worksheet.column_dimensions[col_letter].width = min(max_length + 4, 50)

    output.seek(0)
    return output.read()


def to_json(cleaned_data: dict) -> bytes:
    """Export cleaned data to JSON bytes."""
    rows = extract_rows_from_cleaned(cleaned_data)
    return json.dumps(rows, indent=2, ensure_ascii=False).encode("utf-8")