import json
import requests

def extract_json(html: str, url: str = "") -> dict:
    """
    Extract and parse JSON data from a URL or raw HTML.
    Works for REST API endpoints returning JSON.
    Uses the already-fetched HTML first, avoids a redundant HTTP request.
    """
    # Try parsing the already-fetched HTML as JSON first
    try:
        stripped = html.strip()
        data = json.loads(stripped)
        if isinstance(data, list):
            return {
                "type": "array",
                "count": len(data),
                "data": data[:100],
                "sample": data[:3]
            }
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys()),
                "data": data,
                "sample": data
            }
    except Exception:
        pass

    # Fallback: fetch the URL as JSON (in case the response was HTML-wrapped)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if isinstance(data, list):
            return {
                "type": "array",
                "count": len(data),
                "data": data[:100],
                "sample": data[:3]
            }

        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys()),
                "data": data,
                "sample": data
            }

    except Exception as e:
        return {
            "type": "error",
            "message": f"Could not parse JSON: {str(e)}",
            "data": []
        }

    return {
        "type": "error",
        "message": "Could not parse JSON response",
        "data": []
    }