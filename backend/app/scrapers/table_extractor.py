from bs4 import BeautifulSoup
import pandas as pd

def extract_tables(html: str) -> list:
    """
    Extract all tables from HTML and return as list of dicts.
    Each table becomes a list of row dicts.
    """
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    results = []

    for i, table in enumerate(tables):
        headers = []
        rows = []

        # Extract headers
        header_row = table.find("thead")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        # If no thead, try first tr
        if not headers:
            first_row = table.find("tr")
            if first_row:
                headers = [th.get_text(strip=True) for th in first_row.find_all(["th", "td"])]

        # Extract body rows
        body = table.find("tbody") or table
        for tr in body.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if not cells or cells == headers:
                continue
            if headers and len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
            elif cells:
                rows.append({f"col_{j}": val for j, val in enumerate(cells)})

        if rows:
            results.append({
                "table_index": i,
                "headers": headers,
                "rows": rows,
                "row_count": len(rows)
            })

    return results