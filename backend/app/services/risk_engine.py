"""
Combines three independent signal sources into one risk score. Deliberately
NOT a black box: every point is attributable, which is what "confidence-based
analysis instead of binary detection" (from your slides) actually requires —
you can't produce a defensible confidence score from a single model's softmax.

Scoring is out of 100:
  - Auth forensics (SPF/DKIM/DMARC + header anomalies): up to 35 points
  - Gemini content verdict + confidence:                up to 50 points
  - Infrastructure signals (proxy IP, geo mismatch):     up to 15 points
"""

AUTH_FAIL_WEIGHTS = {"spf": 12, "dkim": 12, "dmarc": 11}

VERDICT_BASE_SCORE = {
    "legitimate": 0,
    "suspicious": 25,
    "phishing": 45,
    "bec": 45,
    "spoofing": 45,
    "malware_delivery": 50,
}


def score_auth_forensics(spf: str, dkim: str, dmarc: str, anomalies: list) -> tuple:
    score = 0
    breakdown = {}

    if spf in ("fail", "softfail"):
        score += AUTH_FAIL_WEIGHTS["spf"]
        breakdown["spf_fail"] = AUTH_FAIL_WEIGHTS["spf"]
    if dkim == "fail":
        score += AUTH_FAIL_WEIGHTS["dkim"]
        breakdown["dkim_fail"] = AUTH_FAIL_WEIGHTS["dkim"]
    if dmarc == "fail":
        score += AUTH_FAIL_WEIGHTS["dmarc"]
        breakdown["dmarc_fail"] = AUTH_FAIL_WEIGHTS["dmarc"]

    # anomalies beyond raw auth failures (reply-to mismatch, display-name spoofing)
    extra_anomalies = max(0, len(anomalies) - sum(1 for a in [spf, dkim, dmarc] if a in ("fail", "softfail")))
    anomaly_score = min(10, extra_anomalies * 5)
    if anomaly_score:
        breakdown["header_anomalies"] = anomaly_score
        score += anomaly_score

    return min(score, 35), breakdown


def score_ai_verdict(verdict: str, confidence: float) -> tuple:
    base = VERDICT_BASE_SCORE.get(verdict, 20)
    contribution = round(base * confidence * (50 / 50), 1)  # confidence-weighted
    # rescale so max possible is 50 (VERDICT_BASE_SCORE max is 50)
    return min(contribution, 50), {"ai_verdict_weighted": contribution}


def score_infrastructure(geo_results: list) -> tuple:
    score = 0
    breakdown = {}
    proxy_count = sum(1 for g in geo_results if g.get("is_proxy"))
    if proxy_count:
        pts = min(10, proxy_count * 5)
        score += pts
        breakdown["proxy_or_hosting_ip"] = pts

    countries = {g.get("country") for g in geo_results if g.get("country")}
    if len(countries) > 1:
        score += 5
        breakdown["multiple_origin_countries"] = 5

    return min(score, 15), breakdown


def compute_risk(spf: str, dkim: str, dmarc: str, anomalies: list,
                  ai_verdict: str, ai_confidence: float,
                  geo_results: list) -> dict:
    auth_score, auth_breakdown = score_auth_forensics(spf, dkim, dmarc, anomalies)
    ai_score, ai_breakdown = score_ai_verdict(ai_verdict, ai_confidence)
    infra_score, infra_breakdown = score_infrastructure(geo_results)

    total = round(auth_score + ai_score + infra_score, 1)
    total = min(total, 100)

    if total >= 75:
        level = "critical"
    elif total >= 50:
        level = "high"
    elif total >= 25:
        level = "medium"
    else:
        level = "low"

    breakdown = {**auth_breakdown, **ai_breakdown, **infra_breakdown}

    return {
        "risk_score": total,
        "risk_level": level,
        "risk_breakdown": breakdown,
        "components": {
            "auth_forensics": auth_score,
            "ai_content_analysis": ai_score,
            "infrastructure": infra_score,
        },
    }
