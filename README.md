# 🏴‍☠️ Black Pearl — AI-Powered Email Threat Detection & Forensic Intelligence

[![SIH 2026 Submission](https://shields.io)](https://github.com)
[![Tech Stack](https://shields.io)](#)

An advanced, end-to-end AI-powered cyber forensics platform designed for **Problem Statement SIH26106**. The platform automates email header parsing, cryptographic authentication checks, multi-hop network routing visualization, and Explainable AI (XAI) threat triage.

---

## 🏗️ Architectural Overview & Modules

| Evaluation Module | Technical Engine |
| :--- | :--- |
| **🤖 AI Threat Classification** | Gemini 3.6 Flash Engine with structured JSON output parsing. |
| **🔍 Header Forensics** | Ingests and extracts `Authentication-Results` and `Received-SPF` headers. |
| **🌐 Infrastructure Mapping** | Multi-hop geospatial network tracing via live node streams. |
| **🕸️ Relationship Graph** | Cross-case entity correlation using **Neo4j**. |
| **⚖️ Admissible Evidence** | Anti-tamper **SHA-256 cryptographic hash-chain ledger** for chain of custody. |

---

## 🚀 Fast-Track Deployment

For the complete project structure and full deployment configurations, please refer to the repository files. Quick setup involves:

1. **Initialize Infrastructure Layer:**
   ```bash
   docker compose up -d
   ```
2. **Launch Backend Analytics Engine:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
3. **Deploy Frontend GUI:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## ⚖️ Compliance
Aligned with Section 63 of the Bharatiya Sakshya Adhiniyam (BSA), 2023 for automated technical certificates and secure chain of custody validation.
