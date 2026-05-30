import pandas as pd
import re
import math

def clean_column_name(col: str) -> str:
    col = str(col).strip().lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = col.strip("_")
    return col if col else "column"


def sanitize_value(val):
    """Convert any non-JSON-safe value to None."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if isinstance(val, str) and val.lower() in ("nan", "none", "null", ""):
        return None
    return val


def sanitize_rows(rows: list) -> list:
    """Sanitize all values in a list of row dicts."""
    cleaned = []
    for row in rows:
        cleaned.append({k: sanitize_value(v) for k, v in row.items()})
    return cleaned


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Fix column names
    df.columns = [clean_column_name(c) for c in df.columns]

    # 2. Remove completely empty rows
    df.dropna(how="all", inplace=True)

    # 3. Remove completely empty columns
    df.dropna(axis=1, how="all", inplace=True)

    # 4. Strip whitespace from string cells
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"": None, "None": None, "nan": None, "NaN": None, "none": None})

    # 5. Remove duplicate rows
    df.drop_duplicates(inplace=True)

    # 6. Try to convert numeric columns
    for col in df.columns:
        try:
            cleaned = df[col].astype(str).str.replace(",", "", regex=False)
            cleaned = cleaned.str.replace(r"[₹$€£%]", "", regex=True).str.strip()
            converted = pd.to_numeric(cleaned, errors="coerce")
            # Only use numeric if more than 50% converted successfully
            if converted.notna().sum() / max(len(converted), 1) > 0.5:
                df[col] = converted
        except Exception:
            pass

    # 7. Reset index
    df.reset_index(drop=True, inplace=True)

    return df


def clean_table_data(rows: list) -> dict:
    if not rows:
        return {"rows": [], "columns": [], "stats": {"original_rows": 0, "cleaned_rows": 0, "removed_rows": 0}}

    original_count = len(rows)

    df = pd.DataFrame(rows)
    df = clean_dataframe(df)

    # Convert to records then sanitize every value
    raw_records = df.to_dict(orient="records")
    cleaned_rows = sanitize_rows(raw_records)
    cleaned_count = len(cleaned_rows)

    return {
        "rows": cleaned_rows,
        "columns": list(df.columns),
        "stats": {
            "original_rows": original_count,
            "cleaned_rows": cleaned_count,
            "removed_rows": original_count - cleaned_count,
            "columns": list(df.columns)
        }
    }


def clean_article_data(article: dict) -> dict:
    if article.get("title"):
        article["title"] = article["title"].strip()

    if article.get("paragraphs"):
        article["paragraphs"] = [
            p.strip() for p in article["paragraphs"]
            if len(p.strip()) > 40
        ]

    if article.get("paragraphs"):
        article["full_text"] = "\n".join(article["paragraphs"])
        article["word_count"] = len(article["full_text"].split())

    if article.get("links"):
        seen = set()
        unique_links = []
        for link in article["links"]:
            if link["url"] not in seen:
                seen.add(link["url"])
                unique_links.append(link)
        article["links"] = unique_links

    return article


def clean_scraped_data(page_type: str, data) -> dict:
    if page_type == "table":
        cleaned_tables = []
        for table in data:
            cleaned = clean_table_data(table.get("rows", []))
            cleaned_tables.append({
                "table_index": table.get("table_index", 0),
                "headers": cleaned["columns"],
                "rows": cleaned["rows"],
                "stats": cleaned["stats"]
            })
        return {
            "page_type": "table",
            "tables": cleaned_tables,
            "total_tables": len(cleaned_tables)
        }

    elif page_type == "article":
        cleaned = clean_article_data(data)
        return {
            "page_type": "article",
            "data": cleaned
        }

    elif page_type == "json":
        if isinstance(data, dict) and data.get("type") == "array":
            rows = data.get("data", [])
            if rows and isinstance(rows[0], dict):
                cleaned = clean_table_data(rows)
                data["data"] = cleaned["rows"]
                data["stats"] = cleaned["stats"]
        return {
            "page_type": "json",
            "data": data
        }

    elif page_type == "pdf":
        if isinstance(data, dict):
            if data.get("full_text"):
                text = data["full_text"]
                text = re.sub(r"\n{3,}", "\n\n", text)
                text = re.sub(r" {2,}", " ", text)
                data["full_text"] = text.strip()
            if data.get("tables"):
                cleaned_tables = []
                for table in data["tables"]:
                    cleaned = clean_table_data(table.get("rows", []))
                    cleaned_tables.append({
                        "page": table.get("page", 1),
                        "headers": cleaned["columns"],
                        "rows": cleaned["rows"],
                        "stats": cleaned["stats"]
                    })
                data["tables"] = cleaned_tables
        return {
            "page_type": "pdf",
            "data": data
        }

    elif page_type in ("amazon_products", "flipkart_products", "products"):
        return {
            "page_type": page_type,
            "data": data
        }

    elif page_type == "jsonld":
        return {
            "page_type": "jsonld",
            "data": data
        }

    return {"page_type": page_type, "data": data}