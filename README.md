# Fresno Carrier Finder

**Fresno Carrier Finder** is a local Python web application designed for non-technical users, business analysts, and researchers to discover businesses in Fresno, California and identify which telephone service providers—specifically **Comcast**, **Xfinity**, and **Comcast Business**—are associated with their telephone numbers.

---

## Table of Contents
1. [Overview & Core Principles](#overview--core-principles)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Windows)](#quick-start-windows)
4. [Google Cloud & Places API Setup](#google-cloud--places-api-setup)
5. [Twilio Lookup API Setup](#twilio-lookup-api-setup)
6. [Application Workflow](#application-workflow)
7. [Carrier Classification Logic](#carrier-classification-logic)
8. [Data Licensing & CSV Export Compliance](#data-licensing--csv-export-compliance)
9. [Cost Controls & Spending Guards](#cost-controls--spending-guards)
10. [Troubleshooting](#troubleshooting)
11. [Project Structure](#project-structure)
12. [Running Automated Tests](#running-automated-tests)

---

## 1. Overview & Core Principles

- **Business Discovery:** Queries the Google Places API (New) across targeted business categories in the Fresno, CA metro area.
- **Phone Validation:** Parses and normalizes telephone numbers into standard E.164 format using the international `phonenumbers` engine.
- **Carrier Intelligence:** Queries the Twilio Lookup v2 API with Line Type Intelligence to obtain verified carrier names and line types (e.g., `landline`, `mobile`, `fixedVoip`).
- **Comcast Detection:** Categorizes phone numbers as **Comcast Match**, **Possible Match**, **Not Match**, or **Unknown**.
- **No-Code Local Web Dashboard:** Minimal Enterprise Utility interface running on `http://127.0.0.1:8765` with sorting, search, column filters, and Excel-ready CSV export.
- **Demo Mode:** Fully functional synthetic Fresno dataset for zero-cost evaluation without any API keys.

---

## 2. Prerequisites

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python 3.11 or later installed (ensure **"Add Python to PATH"** was checked during Python installation)
- **Internet Connection:** Required for API lookups and dependency installation
- **Accounts (For Live Production Searches):**
  - Google Cloud Account with an active billing project
  - Twilio Account with an active billing balance

---

## 3. Quick Start (Windows)

You do **not** need to use the terminal to run normal searches.

### Step 1: Install Dependencies
Double-click:
```text
Install.bat
```
*This checks your Python version, automatically creates a dedicated virtual environment (`.venv`), and installs all required packages (`fastapi`, `uvicorn`, `httpx`, `phonenumbers`, `keyring`, etc.).*

### Step 2: Launch Application
Double-click:
```text
Start App.bat
```
*This launches the local server and automatically opens your default web browser to:*  
`http://127.0.0.1:8765`

### Step 3: Run Your First Scan
1. In the sidebar, select **New Scan**.
2. Keep **Demo Mode** selected to immediately inspect the system with sample Fresno records.
3. Choose your categories (e.g., *Restaurants*, *Dentists*, *Auto Repair*).
4. Click **Start Scan**.
5. When complete, navigate to **Results** to view, filter, inspect, and export the records.

---

## 4. Google Cloud & Places API Setup

To perform live Google Places discoveries:

1. Log in to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `Fresno-Carrier-Discovery`).
3. Link an active billing account (**Billing** is required by Google for Places API access).
4. Navigate to **APIs & Services > Library**.
5. Search for **Places API (New)** and click **Enable**.
6. Navigate to **APIs & Services > Credentials** and click **Create Credentials > API Key**.
7. *(Recommended)* Click **Edit API Key** to restrict its usage to `Places API (New)`.
8. In Fresno Carrier Finder, go to the **Settings** tab.
9. Paste your key into the **Google Places API Key** field.
10. Click **Test Google Places** to verify connectivity.

---

## 5. Twilio Lookup API Setup

To identify telephone carriers using Twilio:

1. Log in to the [Twilio Console](https://console.twilio.com/).
2. Confirm your account has billing credits (Lookup v2 charges ~$0.005 per phone number).
3. Obtain your **Account SID** from the console homepage.
4. Under **Account > API Keys & Tokens**, generate an **API Key SID** and **API Secret**.
5. In Fresno Carrier Finder, open the **Settings** tab.
6. Enter your **Twilio Account SID**, **Twilio API Key SID**, and **Twilio API Secret**.
7. Click **Test Twilio** to verify connectivity.
8. Click **Save Credentials**. Your secrets will be encrypted locally using Windows Credential Manager.

---

## 6. Application Workflow

```text
[Select Categories & Max Limits]
               │
               ▼
   [Business Discovery]
  (Google Places / Licensed Dataset / Demo)
               │
               ▼
 [Phone Normalization (E.164)]
  (Deduplicate & Skip Invalid)
               │
               ▼
   [Carrier Lookup (Twilio)]
  (Bounded Concurrency & Cache)
               │
               ▼
[Comcast Matching & Classification]
               │
               ▼
    [Interactive Dashboard]
  (Filter, Sort, Inspect, Export)
```

---

## 7. Carrier Classification Logic

| Classification | Meaning | API Trigger Conditions |
|---|---|---|
| **Comcast Match** | Strong carrier confirmation | Carrier directly matches `Comcast`, `Xfinity`, `Comcast Business`, `Comcast IP Phone`, `Comcast Cable`, or verified brand aliases. |
| **Possible Match** | Plausible unconfirmed affiliate | Carrier mentions known acquired entities or partners (e.g., `CIMCO`, `Broadwing`, `Unverified Comcast Reseller`). |
| **Not Match** | Verified non-Comcast carrier | Carrier is identified as another known provider (e.g., `AT&T`, `Verizon`, `Spectrum`, `Frontier`, `T-Mobile`). |
| **Unknown** | Inconclusive or missing | Carrier name is blank, omitted, unavailable, or returned an error. |

> **Disclaimer:** A status of "Comcast Match" indicates that the business's telephone number is routed through Comcast/Xfinity carrier infrastructure. It is not legal proof of an active commercial internet or television subscription.

---

## 8. Data Licensing & CSV Export Compliance

Under the **Google Maps Platform Terms of Service**, mass scraping and downloading of business listings to external CSV files is restricted without a specific commercial waiver.

Fresno Carrier Finder implements separate provider pipelines to respect source licenses:

1. **Provider A — Google Places API (New):**
   - Live discovery and real-time dashboard display.
   - Includes Google attribution notices.
   - Bulk CSV downloads from live Google data are blocked with an explanatory compliance notice.

2. **Provider B — Export-Licensed Business Dataset / CSV Import:**
   - Designed for user-owned business lists or licensed B2B directories.
   - Users can upload their own CSV file (`Business Name`, `Address`, `Phone Number`, `Category`).
   - Twilio carrier lookups run normally and CSV export is fully permitted.

3. **Demo Mode:**
   - Synthetic Fresno business listings for zero-cost testing.
   - CSV export is fully enabled.

---

## 9. Cost Controls & Spending Guards

- **Max Businesses Cap:** Restricts the number of listings fetched per scan (default: 50).
- **Max Lookups Cap:** Restricts paid Twilio inquiries per scan (default: 25).
- **Hard Spend Guard:** Halts carrier lookup processing if estimated costs reach the user-defined threshold (default: $5.00).
- **Deduplication:** Multiple businesses sharing the same telephone number share a single carrier lookup, avoiding duplicate charges.
- **Estimated Cost Display:** Displays live Twilio and Google Places fee calculations before and during every scan.

---

## 10. Troubleshooting

### 1. Python not installed / "python is not recognized"
- Download Python 3.11+ from [python.org](https://www.python.org/).
- In the installer, **ensure the checkbox "Add Python to PATH" is checked**.

### 2. Google Places returns 403 or Billing Error
- Verify that billing is linked to your project in the Google Cloud Console.
- Ensure the **Places API (New)** is enabled (not legacy Places API).

### 3. Twilio returns 401 or Auth Error
- Verify that your API Key SID and API Secret are active.
- Ensure your Twilio balance is above $0.00.

### 4. Browser does not open automatically
- Open your browser manually and navigate to:
  `http://127.0.0.1:8765`

### 5. CSV Export Blocked
- If you ran a scan with Google Places, bulk CSV export is disabled per Google ToS.
- Switch to **Licensed Dataset** or **Demo Mode** to generate and export CSV files.

---

## 11. Project Structure

```text
├── app/
│   ├── main.py                     # FastAPI server & route handlers
│   ├── config.py                   # Keyring secrets & Fresno defaults
│   ├── providers/
│   │   ├── base.py                 # Abstract BusinessProvider interface
│   │   ├── google_provider.py      # Provider A: Google Places API (New)
│   │   ├── licensed_provider.py    # Provider B: Licensed dataset & CSV import
│   │   └── demo_provider.py        # Demo Mode: Fresno synthetic dataset
│   ├── services/
│   │   ├── google_places.py        # Google Places Text Search (New) client
│   │   ├── twilio_lookup.py        # Twilio Lookup v2 Line Type Intelligence client
│   │   ├── phone_utils.py          # E.164 normalization & parsing
│   │   ├── carrier_matcher.py      # Comcast & alias classification rules
│   │   ├── scan_manager.py         # Background scan orchestrator & SSE broadcaster
│   │   └── csv_exporter.py         # Excel UTF-8 BOM CSV generator & formula protection
│   ├── static/
│   │   ├── css/style.css           # Minimal Enterprise Utility stylesheet
│   │   └── js/app.js               # Reactive vanilla JS frontend
│   └── templates/
│       └── index.html              # Clean single-page application dashboard
├── sample_data/
│   ├── demo_records.json           # Synthetic Fresno business records
│   ├── fresno_businesses_licensed.csv # Export-eligible Fresno business dataset
│   └── example_export_fresno_comcast.csv # Sample CSV export matching PRD
├── tests/
│   ├── test_phone_utils.py         # Phone parsing & extension tests
│   ├── test_carrier_matcher.py     # Comcast classification tests
│   ├── test_csv_exporter.py        # Excel BOM, formula guard & licensing tests
│   ├── test_scan_manager.py        # Scan lifecycle & cancellation tests
│   └── test_api_endpoints.py       # FastAPI integration tests
├── Install.bat                     # 1-click Windows installer
├── Start App.bat                   # 1-click Windows launcher & browser opener
├── requirements.txt                # Python package dependencies
├── .env.example                    # Sample environment variables
└── README.md                       # Beginner-friendly documentation
```

---

## 12. Running Automated Tests

To run the automated test suite manually:
```cmd
python -m pytest tests/
```
All 20 tests verify phone normalization, Comcast classification rules, CSV formula injection protection, UTF-8 BOM output, scan cancellation, and API endpoint integration.
