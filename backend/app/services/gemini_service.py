"""
Threat classification via Google Gemini. Replaces the scikit-learn/transformers
NLP stack from the original design — Gemini does the phishing/BEC/impersonation
classification, we do NOT train or run any local model.
"""
import json
import logging
import time

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

_client = None

FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
]


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to backend/.env before analyzing email."
            )
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "verdict": {
            "type": "STRING",
            "enum": ["legitimate", "suspicious", "phishing", "bec", "spoofing", "malware_delivery"],
        },
        "confidence": {"type": "NUMBER", "description": "0.0 to 1.0"},
        "reasoning": {"type": "STRING", "description": "2-4 sentence explanation"},
        "indicators": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Specific phrases, tactics or patterns found (e.g. 'urgency language', 'fake invoice request', 'credential harvesting link')",
        },
        "social_engineering_tactics": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
    },
    "required": ["verdict", "confidence", "reasoning", "indicators"],
}

SYSTEM_INSTRUCTION = """You are an email threat analyst inside a SOC forensic platform.
You will be given the subject, sender, and body of an email, plus header-level
authentication signals that have ALREADY been computed (SPF/DKIM/DMARC results
and any anomalies). Your job is ONLY the content/behavioral analysis: does the
text show phishing, business email compromise (BEC), impersonation, social
engineering, or malicious intent? Weigh the provided auth signals as context but
do not just restate them. Be decisive — do not default to 'suspicious' to hedge.
If the email is a normal legitimate message, say so with high confidence.
Respond strictly in the JSON schema provided, nothing else."""


def classify_email(subject: str, sender: str, body_text: str, auth_context: dict) -> dict:
    client = _get_client()

    prompt = f"""EMAIL TO ANALYZE

From: {sender}
Subject: {subject}

Header authentication signals (already verified, not your job to redo this):
- SPF: {auth_context.get('spf')}
- DKIM: {auth_context.get('dkim')}
- DMARC: {auth_context.get('dmarc')}
- Anomalies detected: {auth_context.get('auth_anomalies') or 'none'}

Body:
{body_text[:8000]}
"""

    models_to_try = [settings.GEMINI_MODEL]
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                logger.info("Attempting classification with model: %s (attempt %d)", model_name, attempt + 1)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=RESPONSE_SCHEMA,
                        temperature=0.1,
                    ),
                )
                data = json.loads(response.text)
                data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
                logger.info("Classification succeeded with model %s: verdict=%s, confidence=%.2f", 
                            model_name, data.get("verdict"), data.get("confidence", 0.0))
                return data
            except Exception as e:
                last_error = e
                logger.warning("Gemini model %s attempt %d failed: %s", model_name, attempt + 1, e)
                time.sleep(1)

    logger.exception("All Gemini classification attempts failed: %s", last_error)
    return {
        "verdict": "suspicious",
        "confidence": 0.0,
        "reasoning": f"AI classification unavailable: {last_error}. Falling back to header-forensics-only scoring.",
        "indicators": [],
        "social_engineering_tactics": [],
        "error": str(last_error),
    }
