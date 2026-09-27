# Black Pearl — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence

Working prototype. Real pipeline, real DB, real graph correlation, real
tamper-evident ledger. Gemini replaces the scikit-learn/transformers layer
from the original design — nothing else is mocked out.

## What's real vs. what's simplified (read this before demoing)

| Slide claim | What's actually implemented |
|---|---|
| AI threat detection | Real call to Gemini API, structured JSON verdict/confidence/reasoning |
| SPF/DKIM/DMARC analysis | Reads `Authentication-Results` / `Received-SPF` headers (what the receiving mail server already computed) — does **not** re-run DNS-based SPF/DKIM verification itself. That's what every SOC tool does; re-implementing RFC 7208/6376 from scratch is out of scope for a prototype. |
| IP/domain/geolocation | Real ip-api.com lookups (free tier, no key, 45 req/min) |
| Graph correlation | Real Neo4j — email/domain/IP/URL nodes, shared-infrastructure queries |
| Blockchain evidence ledger | **Not a blockchain.** It's a SHA-256 hash chain in SQLite — same tamper-evidence primitive (each record commits to the previous hash), no distributed consensus. Say this exact sentence if a judge asks. `app/ledger.py` has the full reasoning in comments. |
| Risk/confidence scoring | Real, attributable weighted formula in `app/services/risk_engine.py` — not Gemini's raw confidence, a fusion of auth forensics + AI verdict + infra signals |

## Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for Postgres + Neo4j) — or point at existing instances
- A Gemini API key from https://aistudio.google.com/apikey

## Setup

### 1. Start Postgres + Neo4j
```bash
docker compose up -d
```
Wait ~15s for health checks to pass. Neo4j browser UI: http://localhost:7474 (user `neo4j`, pass `blackpearl123`).

### 2. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — set GEMINI_API_KEY. Everything else works with docker-compose defaults.
uvicorn app.main:app --reload --port 8000
```
Check it's alive: `curl http://localhost:8000/api/health` → `{"status":"ok"}`

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

**Note:** I wrote and syntax/bundle-verified every frontend file with esbuild
in my sandbox (no network access there to run a real `npm install`/dev
server), so import paths and JSX are confirmed correct — but I have not
run the actual dev server end-to-end myself. Run `npm install && npm run dev`
and if anything breaks, send me the exact error and I'll fix it fast rather
than guess.

### 4. Test it
Upload `backend/sample_emails/phishing_sample.eml` through the dashboard.
Expect: SPF/DKIM/DMARC all FAIL, Reply-To domain mismatch flagged, Gemini
verdict should land on `phishing` or `bec`, risk score in the 70s-80s
(critical). If Gemini instead calls it legitimate, that's a real signal to
look at your prompt/model choice, not a bug to paper over.

## API endpoints
- `POST /api/analyze` — upload `.eml`, get full analysis back
- `GET /api/cases` — list all cases
- `GET /api/cases/{id}` — full case detail
- `GET /api/cases/{id}/graph` — Neo4j subgraph for the case
- `GET /api/cases/{id}/related` — other cases sharing IOCs (campaign detection)
- `GET /api/cases/{id}/evidence-trail` — hash-chain ledger entries for the case
- `GET /api/ledger/verify` — walks the entire ledger, recomputes every hash, proves no tampering

## Known gaps — be upfront about these in your demo, don't get caught off guard
1. **No DNS-based SPF/DKIM re-verification.** Relies on the receiving server's Authentication-Results header. If a test email lacks that header (e.g. you hand-craft an `.eml` without it), SPF/DKIM/DMARC will show `none`, not `fail`.
2. **No WHOIS enrichment.** IOC table shows geolocation (ip-api.com) but not WHOIS registrant data — slides mention WHOIS, code doesn't call it yet. Straightforward to add (`app/services/geo_service.py` is the place) if you need it before submission.
3. **ip-api.com free tier is rate-limited** (45 req/min) and HTTP-only (not HTTPS) — fine for a demo, swap `GEO_API_BASE` for a paid provider before anything resembling production use.
4. **Gemini 2.5 shuts down Oct 16, 2026.** Default model in `.env.example` is `gemini-2.5-flash`. If you're setting this up after that date, change `GEMINI_MODEL` to whatever's current stable (`gemini-3-flash-preview` as of writing) — one env var, no code change.
5. **Graph correlation only works across cases you've already analyzed.** Upload a few different phishing samples that share a sender domain or IP to actually see the "Related Campaign Cases" panel populate.
6. **No auth/access control on the API.** Anyone who can reach port 8000 can upload and read every case. Fine for a hackathon demo, not fine for real email data — add auth before this touches production traffic.

## Project structure
```
backend/
  app/
    main.py              FastAPI app, CORS, startup DB/Neo4j init
    config.py             env-driven settings
    database.py            Postgres/SQLAlchemy session
    models.py               Case + IOC ORM models
    schemas.py               Pydantic response models
    ledger.py                 SHA-256 hash-chain evidence ledger (SQLite)
    neo4j_client.py            graph correlation
    routes.py                   orchestrates the whole pipeline
    services/
      email_parser.py           .eml parsing, header forensics, IOC extraction
      gemini_service.py          Gemini API threat classification
      geo_service.py              IP geolocation
      risk_engine.py               fuses everything into one attributable score
  sample_emails/phishing_sample.eml
  docker-compose.yml (repo root)
frontend/
  src/
    pages/Dashboard.jsx, CaseDetail.jsx
    components/UploadBox, IOCTable, RiskGauge, GraphView, CaseList
    api.js
```
