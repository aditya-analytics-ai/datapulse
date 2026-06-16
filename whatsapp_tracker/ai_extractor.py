"""
ai_extractor.py — Resilient AI job extractor.
Tries Gemini first → automatically falls back to Groq (Llama 3) on any failure.
Both are free. Zero downtime even if one service has quota/region issues.
"""
import json
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Clients (lazy-initialized) ────────────────────────────────────────────────
_gemini_client = None
_groq_client   = None

def _gemini(api_key: str):
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

def _groq(api_key: str):
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ── Shared prompt builder ─────────────────────────────────────────────────────
def _build_prompt(message_text: str, profile: dict) -> str:
    return f"""You are a job posting analyzer for the Indian job market.
Analyze the WhatsApp message and return ONLY valid JSON — no markdown, no explanation.

WhatsApp Message:
\"\"\"{message_text[:2000]}\"\"\"

Candidate Profile:
- Looking for: {", ".join(profile["roles"])}
- Skills: {", ".join(profile["skills"])}
- Location preference: {profile["location"]}
- Experience: {profile["experience"]}
- Minimum salary: {profile["salary_min_lpa"]} LPA

If NOT a job posting → return exactly: {{"is_job": false}}

If it IS a job posting → return:
{{
  "is_job": true,
  "title": "job title or null",
  "company": "company name or null",
  "skills": ["skill1", "skill2"],
  "salary": "salary string or null",
  "location": "location or null",
  "contact": "phone/email or null",
  "apply_link": "URL or null",
  "job_type": "Full-time | Part-time | Internship | Freelance | null",
  "experience_required": "e.g. 2-4 years or null",
  "relevance_score": <integer 0-100>,
  "relevance_reason": "one sentence"
}}

Score: 80-100 = strong match, 50-79 = partial, 0-49 = weak.
Return ONLY the JSON object, nothing else."""


def _parse_json(raw: str) -> dict | None:
    """Safely parse JSON, stripping markdown fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed[0] if parsed else None
        return parsed
    except json.JSONDecodeError:
        # Try to salvage partial JSON
        try:
            start = raw.index("{")
            end   = raw.rindex("}") + 1
            parsed = json.loads(raw[start:end])
            if isinstance(parsed, list):
                return parsed[0] if parsed else None
            return parsed
        except Exception:
            return None


# ── Primary: Gemini ───────────────────────────────────────────────────────────
def _try_gemini(prompt: str, api_key: str) -> str:
    client = _gemini(api_key)
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return resp.text


def _try_gemini_vision(image_bytes: bytes, api_key: str) -> str:
    """Extract text from image using Gemini vision."""
    client = _gemini(api_key)
    import base64
    b64 = base64.b64encode(image_bytes).decode()
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "Extract ALL text from this image. Return only the extracted text, no explanation.",
            {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
        ],
    )
    return resp.text


# ── Fallback: Groq (Llama 3) ─────────────────────────────────────────────────
def _try_groq(prompt: str, api_key: str) -> str:
    client = _groq(api_key)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512,
    )
    return resp.choices[0].message.content


# ── Public API ────────────────────────────────────────────────────────────────
def extract_job(
    message_text: str,
    profile: dict,
    gemini_api_key: str,
    groq_api_key: str = "",
) -> dict | None:
    """
    Extract structured job data from a WhatsApp message.
    Tries Gemini first → falls back to Groq automatically.
    Returns a parsed dict or None on total failure.
    """
    prompt = _build_prompt(message_text, profile)
    raw    = None

    # 1 — Try Gemini
    if gemini_api_key:
        try:
            print("    [Gemini]...", end=" ", flush=True)
            raw = _try_gemini(prompt, gemini_api_key)
            print("OK")
        except Exception as e:
            print(f"FAIL ({type(e).__name__}) -> switching to Groq")
            raw = None

    # 2 — Groq fallback
    if raw is None and groq_api_key:
        try:
            print("    [Groq]...", end=" ", flush=True)
            raw = _try_groq(prompt, groq_api_key)
            print("OK")
        except Exception as e:
            print(f"FAIL ({type(e).__name__})")
            return None

    if raw is None:
        print("    [!] No AI provider available.")
        return None

    return _parse_json(raw)


# ── Vision OCR ─────────────────────────────────────────────────────────────────
def extract_text_from_image(
    image_bytes: bytes,
    gemini_api_key: str,
    groq_api_key: str = "",
) -> str:
    """
    Extract text from image using AI vision.
    Tries Gemini first (supports vision) → falls back to local OCR if needed.
    """
    # 1 — Try Gemini Vision
    if gemini_api_key:
        try:
            print("    [Gemini Vision]...", end=" ", flush=True)
            text = _try_gemini_vision(image_bytes, gemini_api_key)
            print("OK")
            return text.strip()
        except Exception as e:
            print(f"FAIL ({type(e).__name__})")

    # 2 — Fallback: Local Tesseract (optional)
    try:
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes)).convert('L')
        text = pytesseract.image_to_string(img)
        if text.strip():
            print("    [Tesseract] OK")
            return text.strip()
    except Exception:
        pass

    return ""
