# GradGate v2 - Project Handover

## Project Overview

**GradGate** is a graduation requirement audit system for CSE students. Built in **Phase 1-6** of the project.

### Tech Stack
- **Backend**: FastAPI + Supabase (PostgreSQL + Auth)
- **Web App**: Vite + React + Tailwind CSS
- **Mobile App**: Expo React Native + Google OAuth
- **OCR**: Tesseract for transcript scanning
- **Load Testing**: Locust

### Current Location
```
/Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/
```

---

## Current Status (as of Mar 8, 2026)

### Running Servers
```bash
# API Server (port 8000)
uvicorn api.main:app --reload --port 8000 --host 0.0.0.0

# Web App (port 5173)
npm run dev
```

### Environment
- `.env` file at `GradGate-v2/.env`
- **TEST_MODE=true** (bypasses JWT auth for local dev)
- Supabase URL: `https://mdgjncmjvlrhkygcppej.supabase.co`

---

## What Was Built

### Phase 2: Backend
- FastAPI with Supabase integration
- JWT authentication (via `api/auth.py`)
- Endpoints:
  - `/audit/csv` - Upload CSV transcript for audit
  - `/audit/image` - Upload image for OCR processing

### Phase 3: OCR Pipeline
- Tesseract integration for transcript scanning
- Located in `cli/audit/`

### Phase 4: Web App
- Vite + React + Tailwind CSS
- Theme: Parchment background (#FAF8F5), Ink text (#1A1714)
- Pages: Login, Dashboard (upload), Testing, Profile

### Phase 5: Mobile App
- Expo React Native (in progress)
- Google OAuth setup

### Phase 6: Load Testing
- Locust infrastructure for 20 concurrent users

---

## Outstanding Issues

### 🔴 CRITICAL: Audit Showing Wrong Results

**Problem**: Audit shows courses as "missing" when they're actually in the uploaded CSV.

**Details**:
- User uploads `tc01_cse_all_pass.csv` (contains courses like HIS102, PHI104, BIO103)
- When tested via API with real auth token: Returns `Eligible: False`, `Missing courses: (empty)`, reason: `Need 3.0 more credits (133.0/136)`
- When user logs in via webapp and uploads: Shows many missing courses (different result)

**Suspected Cause**: The webapp is processing the CSV differently than the direct API call.

**Debug Steps**:
1. Check uvicorn logs when user makes request through webapp
2. Verify how the file is being sent from `Dashboard.jsx`
3. Compare the data flow between webapp → API vs direct API call

---

## Pending Tasks

1. **Fix Audit Bug** - Debug why audit shows different results via webapp vs API
2. **Set TEST_MODE=false** - Change in `.env` and restart server to save to real DB
3. **Deploy for Demo** - Deploy webapp and API

---

## Key Files

| File | Purpose |
|------|---------|
| `api/routers/audit.py` | Audit logic - where the bug likely is |
| `api/auth.py` | JWT auth + TEST_MODE setting |
| `webapp/src/pages/Dashboard.jsx` | File upload UI |
| `webapp/src/pages/Testing.jsx` | Testing/audit results display |
| `.env` | Environment config (TEST_MODE) |
| `cli/audit/transcript_audit.py` | Core audit algorithm |

---

## Recent Changes Made

1. **Testing.jsx** - Fixed white text color for light theme
2. **index.css** - Fixed @import warning by moving fonts to index.html
3. **audit.py** - Added TEST_MODE logic to skip DB saves
4. **Supabase** - Added mobile OAuth redirect URLs

---

## How to Continue

1. Check server logs: `uvicorn api.main:app` output
2. Reproduce the issue via webapp upload
3. Compare with direct API call: `curl -X POST http://localhost:8000/audit/csv ...`
4. Trace through `Dashboard.jsx` → API → `audit.py`

---

## Uncommitted Changes (git status)

```
modified:   ../.DS_Store
modified:   GradGate-v2/webapp/index.html      (title + fonts)
modified:   GradGate-v2/webapp/src/index.css   (font imports)
modified:   GradGate-v2/webapp/src/pages/Testing.jsx (color fix)
```

---

## Notes

- OCR setup may need system-level Tesseract installation
- Load testing scripts in `tests/load/` directory
- Mobile app requires Expo Go for testing
