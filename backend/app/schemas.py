from typing import Optional
from pydantic import BaseModel


class IOCOut(BaseModel):
    ioc_type: str
    value: str
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    isp: Optional[str] = None
    org: Optional[str] = None
    is_proxy: Optional[bool] = None

    class Config:
        from_attributes = True


class CaseSummaryOut(BaseModel):
    id: str
    created_at: str
    filename: Optional[str]
    subject: Optional[str]
    sender: Optional[str]
    risk_score: Optional[float]
    risk_level: Optional[str]
    ai_verdict: Optional[str]

    class Config:
        from_attributes = True


class CaseDetailOut(BaseModel):
    id: str
    created_at: str
    filename: Optional[str]
    subject: Optional[str]
    sender: Optional[str]
    sender_domain: Optional[str]
    to_addr: Optional[str]

    spf_result: Optional[str]
    dkim_result: Optional[str]
    dmarc_result: Optional[str]
    relay_path: Optional[list]
    auth_anomalies: Optional[list]

    ai_verdict: Optional[str]
    ai_confidence: Optional[float]
    ai_reasoning: Optional[str]
    ai_indicators: Optional[list]

    risk_score: Optional[float]
    risk_level: Optional[str]
    risk_breakdown: Optional[dict]

    evidence_hash: Optional[str]
    ledger_seq: Optional[int]

    iocs: list[IOCOut] = []

    class Config:
        from_attributes = True
