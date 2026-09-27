import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, TypeDecorator
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class JSONType(TypeDecorator):
    """Stores JSON as TEXT — works on both Postgres and SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, default=str)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=gen_uuid)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    filename = Column(String, nullable=True)
    subject = Column(Text, nullable=True)
    sender = Column(String, nullable=True)
    sender_domain = Column(String, nullable=True)
    to_addr = Column(String, nullable=True)
    raw_headers = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)

    # Header forensics
    spf_result = Column(String, nullable=True)
    dkim_result = Column(String, nullable=True)
    dmarc_result = Column(String, nullable=True)
    relay_path = Column(JSONType, nullable=True)   # list of hops in order
    auth_anomalies = Column(JSONType, nullable=True)

    # AI verdict (Gemini)
    ai_verdict = Column(String, nullable=True)       # phishing / bec / spoofing / legitimate / suspicious
    ai_confidence = Column(Float, nullable=True)      # 0-1
    ai_reasoning = Column(Text, nullable=True)
    ai_indicators = Column(JSONType, nullable=True)      # list of strings model flagged

    # Risk engine output
    risk_score = Column(Float, nullable=True)         # 0-100
    risk_level = Column(String, nullable=True)        # low / medium / high / critical
    risk_breakdown = Column(JSONType, nullable=True)      # {component: contribution}

    # Evidence
    evidence_hash = Column(String, nullable=True)
    ledger_seq = Column(Integer, nullable=True)

    iocs = relationship("IOC", back_populates="case", cascade="all, delete-orphan")


class IOC(Base):
    __tablename__ = "iocs"

    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)

    ioc_type = Column(String, nullable=False)   # ip / domain / url / hash
    value = Column(String, nullable=False)

    # Enrichment (IP only)
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    city = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    isp = Column(String, nullable=True)
    org = Column(String, nullable=True)
    is_proxy = Column(String, nullable=True)

    case = relationship("Case", back_populates="iocs")
