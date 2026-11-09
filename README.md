# CarrierPulse — Commercial Telecom Discovery & Line Verification Platform
*(Pre-configured Profile: Fresno, CA Central Valley & Comcast / Xfinity Intelligence)*

**CarrierPulse** is an enterprise-grade commercial telecom intelligence platform designed for business analysts, telecommunications sales teams, and competitive researchers. It discovers commercial business establishments across target metropolitan markets, standardizes contact telemetry, and audits carrier assignments via official carrier registries (such as Twilio Lookup v2 Line Type Intelligence).

This repository comes **pre-configured with a turnkey regional profile for Fresno, California (Area 559)** and an active carrier detection pattern for **Comcast, Xfinity, and Comcast Business**.

---

## Table of Contents
1. [Overview & Core Architecture](#overview--core-architecture)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Windows)](#quick-start-windows)
4. [Google Cloud & Places API Setup](#google-cloud--places-api-setup)
5. [Twilio Lookup API Setup](#twilio-lookup-api-setup)
6. [Multi-Metro & Target Carrier Intelligence](#multi-metro--target-carrier-intelligence)
7. [Application Workflow](#application-workflow)
8. [Carrier Classification Logic](#carrier-classification-logic)
9. [Data Licensing & CSV Export Compliance](#data-licensing--csv-export-compliance)
10. [Cost Controls & Spending Guards](#cost-controls--spending-guards)
11. [Troubleshooting](#troubleshooting)
12. [Project Structure](#project-structure)
13. [Running Automated Tests](#running-automated-tests)

---

## 1. Overview & Core Architecture

- **Commercial Entity Discovery:** Integrates with the Google Places API (New) across targeted business verticals (Restaurants, Dentists, Auto Repair, Plumbers, Law Firms & Professional Offices).
- **International Phone Normalization:** Cleans, validates, and standardizes local phone numbers into universal E.164 format via the Google-developed `phonenumbers` engine.
- **Carrier Telemetry & Line Type Intelligence:** Communicates directly with Twilio Lookup v2 Line Type Intelligence to resolve underlying network operators and infrastructure types (`fixedVoip`, `landline`, `mobile`).
- **Target Carrier Matching Heuristics:** Employs multi-tier fuzzy and direct alias matching to classify carriers as **Target Match** (e.g. Comcast/Xfinity), **Possible Match**, **Not Match**, or **Unknown**.
- **Interactive Executive Dashboard:** A clean, modern Single-Page Application (SPA) dashboard with Leaflet geolocation mapping, company telemetry inspection cards, and instant filtering.
- **Zero-Config Demo Mode:** Ships with a full synthetic multi-category dataset allowing non-technical evaluators to test discovery, mapping, and Excel CSV exports immediately without API keys.

---

## 2. Prerequisites

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python 3.11 or later installed (ensure **"Add Python to PATH"** is checked during installation)
- **Internet Access:** Required for dependency setup and live registry queries
- **Optional (For Live External Queries):**
  - Google Cloud Account with Places API (New) enabled
  - Twilio Account with Lookup v2 Line Type Intelligence active

---

## 3. Quick Start (Windows)

No command-line experience is required.

### Step 1: Automated Installation
Double-click:
```text
Install.bat
```
*This validates your Python environment, builds a self-contained virtual environment (`.venv`), and installs all required dependencies (`fastapi`, `uvicorn`, `phonenumbers`, `keyring`, etc.).*

### Step 2: Launch Platform
Double-click:
```text
Start App.bat
```
*This starts the local FastAPI server and automatically opens your default web browser to:*  
`http://127.0.0.1:8765`

### Step 3: Run Discovery Audit
1. Click **New Scan** in the top navigation.
2. Select your data source (Demo Mode is selected by default for zero-cost evaluation).
3. Review your target business categories.
4. Click **Start Scan** to stream live discoveries and carrier resolutions.
5. In the **Dashboard** or **Results Table**, inspect company coordinates, telephone pipeline health, and click **Export CSV**.

---

## 4. Google Cloud & Places API Setup

To enable live business discoveries in target markets:

1. Sign in to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (e.g., `CarrierPulse-Discovery`).
3. Ensure an active billing account is linked.
4. Go to **APIs & Services > Library**, search for **Places API (New)**, and click **Enable**.
5. Go to **APIs & Services > Credentials** and click **Create Credentials > API Key**.
6. In CarrierPulse, navigate to the **Settings** tab.
7. Paste your key into the **Google Places API Key** field and click **Test Google**.

---

## 5. Twilio Lookup API Setup

To resolve carrier networks and PBX line types:

1. Sign in to the [Twilio Console](https://console.twilio.com/).
2. Confirm active account balance (Twilio charges ~$0.005 per Line Type Intelligence query).
3. Copy your **Account SID** from the console overview.
4. Navigate to **Account > API Keys & Tokens** and create an **API Key SID** and **API Secret**.
5. In CarrierPulse, open the **Settings** tab.
6. Enter your credentials, click **Test Twilio**, and click **Save Credentials**.
7. Credentials are encrypted locally via the Windows Credential Manager.

---

## 6. Multi-Metro & Target Carrier Intelligence

CarrierPulse is architected for regional flexibility across California Central Valley and beyond:

| Metro Region | Coordinate Anchor | Search Radius | Default Area Codes |
|---|---|---|---|
| **Fresno, CA (Default)** | 36.7468° N, 119.7725° W | 25 km (Metro & Clovis) | 559 |
| **Bakersfield, CA** | 35.3732° N, 119.0187° W | 25 km Metro | 661 |
| **Sacramento, CA** | 38.5815° N, 121.4943° W | 30 km Metro | 916, 279 |
| **Modesto, CA** | 37.6390° N, 120.9968° W | 20 km Metro | 209 |
| **Custom Region** | User Specified | User Specified | Any |

### Supported Carrier Detection Filters:
- **Comcast & Xfinity (Default Profile):** Detects Comcast Cable, Comcast Business Communications, Comcast IP Phone, CIMCO, and verified operating subsidiaries.
- **AT&T California:** Audits lines on AT&T Corp, SBC, Pacific Bell, and Ameritech.
- **Charter / Spectrum:** Tracks Charter Communications, Time Warner Cable, and Bright House.
- **All Commercial Carriers:** Comprehensive multi-carrier audit outputting complete telecom infrastructure attribution.

---

## 7. Application Workflow

```text
[Select Metro & Target Carrier Filter]
                 │
                 ▼
     [Entity Discovery Phase]
(Google Places / Licensed B2B CSV / Demo)
                 │
                 ▼
   [E.164 Telemetry Normalization]
    (Deduplication & Validity Checks)
                 │
                 ▼
   [Carrier Registry Intelligence]
     (Twilio Lookup v2 Pipeline)
                 │
                 ▼
  [Algorithmic Carrier Attribution]
  (Target Match / Possible / Non-Match)
                 │
                 ▼
      [Executive Dashboard & Map]
    (Excel-Ready UTF-8 BOM CSV Export)
```

---

## 8. Carrier Classification Logic

| Classification | Meaning | Attribution Triggers |
|---|---|---|
| **Comcast Match** | Direct carrier attribution | Operating network strictly matches `Comcast`, `Xfinity`, `Comcast Business`, `Comcast IP Phone`, `Comcast Cable Communications`, or verified carrier CIDs. |
| **Possible Match** | Plausible affiliate or reseller | Carrier resolves to an affiliated partner, historical acquisition (e.g., `CIMCO Communications`), or unverified regional reseller. |
| **Not Match** | Verified alternative network | Number is operated by a competing carrier (e.g. `AT&T`, `Verizon`, `Charter Spectrum`, `Frontier`, `Lumen`). |
| **Unknown** | Unresolved telemetry | Carrier field is unavailable, omitted, or registry query encountered an error. |

> **Audit Note:** A "Comcast Match" attribution verifies that the business's public phone number routes through Comcast/Xfinity telecommunications infrastructure. It serves as a high-confidence operational indicator of enterprise service.

---

## 9. Data Licensing & CSV Export Compliance

CarrierPulse strictly adheres to commercial data platform guidelines:

1. **Provider A — Google Places API (New):**
   - Real-time map rendering and visual telemetry.
   - Includes standard provider attribution.
   - Mass CSV dumping from raw Google Places results is restricted per Google Maps Platform policies.

2. **Provider B — Export-Licensed Commercial Datasets / CSV Upload:**
   - Engineered for commercial B2B directories, customer CRM lists, or licensed records.
   - Twilio carrier lookups run across custom imports and CSV exports are fully unrestricted.

3. **Provider C — Zero-Cost Demo Mode:**
   - Pre-loaded multi-category synthetic records for complete feature evaluation and CSV export testing.

---

## 10. Cost Controls & Spending Guards

- **Business Discovery Ceiling:** Maximum listing query cap (default: 50).
- **Lookup Query Cap:** Maximum paid carrier registry queries (default: 25).
- **Automated Spend Guard:** Safety limit preventing registry charges from exceeding a set ceiling (default: $5.00).
- **Telephone Deduplication:** Multiple listings operating the same phone number share a single lookup to eliminate duplicate costs.
- **Pre-Execution Cost Estimator:** Real-time billing projection displayed before initiating any live scan.

---

## 11. Troubleshooting

### 1. Python is not recognized in terminal / batch launcher
- Download Python 3.11+ from [python.org](https://www.python.org/).
- In the installer, **ensure "Add Python to PATH" is checked**.

### 2. Google Places returns 403 / Billing Error
- Confirm your Google Cloud project is linked to an active credit card or billing account.
- Confirm **Places API (New)** is enabled in API Library.

### 3. Twilio authentication failure
- Verify Account SID, API Key SID, and API Secret.
- Confirm account has positive prepaid balance.

### 4. CSV Export shows compliance notification
- When running live Google Places discoveries, CSV lead extraction is blocked by Google's Terms of Service.
- Switch to **Licensed Dataset** or **Demo Mode** to download CSV exports.

---

## 12. Project Structure

```text
├── app/
│   ├── main.py                     # FastAPI server & route handlers
│   ├── config.py                   # Keyring secrets & multi-metro configuration
│   ├── providers/
│   │   ├── base.py                 # Abstract BusinessProvider interface
│   │   ├── google_provider.py      # Provider A: Google Places API (New)
│   │   ├── licensed_provider.py    # Provider B: Licensed dataset & CSV import
│   │   └── demo_provider.py        # Demo Mode: Synthetic multi-category dataset
│   ├── services/
│   │   ├── google_places.py        # Google Places Text Search (New) client
│   │   ├── twilio_lookup.py        # Twilio Lookup v2 Line Type Intelligence client
│   │   ├── phone_utils.py          # E.164 normalization & parsing
│   │   ├── carrier_matcher.py      # Multi-tier carrier classification heuristics
│   │   ├── scan_manager.py         # Background scan orchestrator & SSE broadcaster
│   │   └── csv_exporter.py         # Excel UTF-8 BOM CSV generator & formula protection
│   ├── static/
│   │   ├── css/style.css           # Clean modern dashboard stylesheet
│   │   └── js/app.js               # Reactive single-page application frontend
│   └── templates/
│       └── index.html              # Leaflet & telemetry dashboard template
├── sample_data/
│   ├── demo_records.json           # Pre-loaded multi-category business records
│   ├── fresno_businesses_licensed.csv # Export-eligible commercial dataset
│   └── example_export_fresno_comcast.csv # Sample verified CSV export
├── tests/
│   ├── test_phone_utils.py         # Phone parsing & extension tests
│   ├── test_carrier_matcher.py     # Carrier classification tests
│   ├── test_csv_exporter.py        # Excel BOM, formula guard & licensing tests
│   ├── test_scan_manager.py        # Scan lifecycle & cancellation tests
│   └── test_api_endpoints.py       # FastAPI integration tests
├── Install.bat                     # 1-click Windows installer
├── Start App.bat                   # 1-click Windows launcher & browser opener
├── requirements.txt                # Python package dependencies
├── .env.example                    # Sample environment variables
└── README.md                       # Comprehensive platform documentation
```

---

## 13. Running Automated Tests

To execute the test suite:
```cmd
python -m pytest tests/
```
All 20 unit and integration tests verify phone normalization, carrier matching logic, CSV formula injection protection, UTF-8 BOM formatting, and API endpoint stability.
