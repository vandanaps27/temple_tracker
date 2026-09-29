# 🛕 Temple Income & Expenditure Tracker

A responsive, cross-platform database dashboard client engineered using the **Python Flet** UI framework. The system provides a seamless front-end interface for temple administrators, feeding financial records directly into a cloud database hosted entirely on **Google Sheets**.

---

## 🚀 Key Architectural Features

- **Multi-Threaded Background Sync:** The user interface renders instantly on launch with a temporary `"Synchronizing..."` state. Database connectivity operations execute asynchronously in an isolated background thread, preventing UI freezing or frame lagging due to network latency.
- **Modern Flet Navigation Matrix:** Fully structured to align with modern Flet layout engines, using a dedicated component layout scheme for flexible rendering across Desktop, Web, and Mobile Viewports.
- **Bi-Directional Cloud Pipeline:** Connects directly via secure Google Service Accounts (`service_account.json`) to automate remote read/write cycles instantly.

---

## 🗺️ Functional Workspace Zones

### 1. 💰 Income Logger Form
- Designed for rapid bookkeeping entry to log all incoming financial contributions.
- Features an adaptive **Source Type Selector**. Selecting `"Committee"` automatically fetches the current roster from the cloud and replaces the open text box with a clean dropdown menu of active member profiles.

### 2. 📉 Expense Logger Form
- A ledger input panel built to track structural outlays and vendor receipts.
- Categorizes all outgoing spending parameters dynamically *(e.g., Pooja Materials, Maintenance, Salaries / Dakshina, Festivals)* with built-in metadata descriptions.

### 3. 📊 Accounts Breakdown & Deletion Engine
- Generates historical monthly financial statements based on target Month/Year configurations.
- Displays calculated metrics for **Total Monthly Income**, **Total Monthly Expense**, and **Net Savings**.
- Features an integrated **Trash Icon Row Deletion Tool**. Clicking the delete trigger maps the row coordinate data, prompts an interactive confirmation safety dialog, and erases the matching entry directly from the live Google Sheets ledger.

### 4. ⚠️ Deficit Tracker (Pending Dues)
- An automated financial audit mechanism for committee tracking.
- Scans the core committee pledge matrix, cross-references historical payments logged under the `"Committee"` flag for the target month, and outputs a dynamic data table highlighting names, exact amounts paid, and red-alert balance deficits still owed.

---

## 📅 Google Sheets Database Schema

The system relies on a single central spreadsheet workbook file named **`FletDataSheet`** split into three dedicated worksheets:

| Worksheet | Required Schema Fields (Columns A, B, C...) |
| :--- | :--- |
| **`income`** | `Date`, `Source Type`, `Name`, `Amount`, `Description` |
| **`expenses`** | `Date`, `Category`, `Amount`, `Description` |
| **`committee`** | `Name`, `Monthly Pledge` |

---

## 🛠️ Step-by-Step Local Deployment

### 1. Repository Setup & Dependencies
Ensure you have Python 3.10+ installed on your computer. Clone this project folder, open your terminal workspace inside it, and run:
```bash
pip install flet gspread google-auth
```

### 2. Google Cloud Service Account Configuration
To enable database handshakes, you must provision an authentication credential:
1. Navigate to the [Google Cloud Console](https://google.com).
2. Create a new project and enable the **Google Drive API** and **Google Sheets API**.
3. Generate a **Service Account** credential set and download the resulting private key configuration file.
4. Rename that downloaded document to **`service_account.json`**.
5. Place the file inside your project's root folder (or inside an `assets/` subdirectory if packing for mobile deployments).
6. Open your `service_account.json` file, copy the unique `client_email` string value inside it, and **Share your Google Sheet (`FletDataSheet`) with that email address** giving it full *Editor* privileges.

### 3. Running the App
Execute the main thread wrapper script directly from your terminal shell:
```bash
python main.py
```

---

## 📦 Packaging and Distribution

### 🪟 Windows One-Click Execution Launcher
To launch the system instantly without running manual terminal commands, create a file named `run_tracker.bat` inside your project folder containing:
```cmd
@echo off
cd /d "%~dp0"
title Starting Temple Tracker Dashboard...
python main.py
if %errorlevel% neq 0 (
    echo Application engine crashed or encountered a runtime error.
    pause
)
```
Double-clicking this `.bat` script wakes up the framework layout and brings up the dashboard UI instantly.

### 🤖 Compiling to an Android APK
To compile the system into a shareable mobile `.apk` installation package:
1. Ensure a configuration profile named `flet.yaml` exists in the folder containing:
   ```yaml
   android:
     permissions:
       - android.permission.INTERNET
   ```
2. Move your `service_account.json` inside a folder path named `assets/` and verify your `TARGET_JSON_PATH` points there.
3. Execute the compiler command:
   ```bash
   flet build apk
   ```
The finalized executable will be located inside your local tree workspace at `build/apk/app-release.apk`.
