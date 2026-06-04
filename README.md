# Monster Radar & Portfolio Tracker

An integrated event-driven automation suite combining **retail web scraping**, **real-time geolocation telemetry**, and **AI assistant integrations** deployed via **n8n** and **Python** on a containerized cloud infrastructure.

## 🚀 Architecture Overview

This project consists of two core automation pipelines designed to demonstrate enterprise-grade workflow orchestration, API integrations, and secure data handling.

```mermaid
graph TD
    %% Monster Radar Pipeline
    subgraph Monster Radar (B2C Retail Monitoring)
        A[Schedule Trigger] -->|Twice Daily| B[Scrape zlacnene.sk]
        B --> C[Parse Discount Data]
        C --> D[Deduplicate Alert]
        D -->|New Discounts| E[Store in DB]
        D -->|Notify Subscribers| F[Telegram Bot API]
        F -->|Request Graph| G[QuickChart.io API]
        G -->|Visual Trend| F
    end

    %% Portfolio Tracker Pipeline
    subgraph Portfolio Tracker (B2B Telemetry & CRM)
        H[Website Frontend] -->|AJAX Webhook| I[Normalize Geolocation]
        I -->|Filter out User IP| J{Self Visitor?}
        J -->|No| K[Query ipwho.is HTTPS]
        J -->|Yes| L[Ignore / Stop]
        K --> M[Geotag & Rich Footprint]
        M --> N[Log DB & CRM]
        M --> O[Telegram Admin Alert]
    end
```

### 1. 🥤 Monster Radar (B2C Retail SaaS)
- **Automated Scraping:** Periodically extracts energy drink prices across Slovak supermarkets (Tesco, Kaufland, Lidl, Billa) using resilient parsing logic.
- **Dynamic Charting:** Accumulates price history and uses the QuickChart.io API to generate multi-line trend charts.
- **Monetization & CRM:** Integrates the Telegram Stars API for premium subscriptions, syncing payments with a Google Sheets CRM.

### 2. 📡 Portfolio Tracker (Silent Geolocation Telemetry)
- **AJAX Footprint:** Captures anonymous website events (page loads, CV downloads, link clicks) and sends JSON payloads to an n8n webhook.
- **IP Geolocation Enrichment:** Resolves visitor details (city, country, ISP, ASN, VPN/proxy flags) using the `ipwho.is` HTTPS API.
- **Defensive Noise Filtering:** Features custom JavaScript filters to drop self-visitor transactions, avoiding bot spam.
- **Admin Alerts:** Sends formatted HTML alerts with direct Google Maps search coordinates to the developer.

---

## 🛠 Tech Stack

- **Orchestration:** n8n Workflow Engine (Self-hosted on Docker)
- **Server Environment:** Hetzner Cloud VM (Ubuntu Noble-Numbat), Nginx reverse proxy, SSL/TLS Let's Encrypt
- **Scripts:** Python (automation setups, deployments, and checks)
- **Database:** SQLite (n8n persistence and local tracking backups)
- **External Integrations:** Google Sheets API, Google Vertex AI, Telegram Bot API, Telegram Stars payment gateways, QuickChart.io

---

## 📂 Repository Structure

- `workflows/`: Exported JSON n8n blueprint flows.
  - `monster_hunter_workflow.json`: Retail price monitor with Telegram Stars checkouts.
  - `portfolio_tracker_workflow.json`: Safe geolocation visitor tracker.
- `scripts/`: Diagnostic and deployment Python modules.
  - `fix_user_ip_filter.py`: Automatic user IP whitelist injection.
  - `check_geo_details.py`: Verification script for geolocation payloads.
  - `deploy_website.py`: Frontend assets SFTP sync.
