# GradGate v2 — Revised Implementation Plan

## Confirmed Tech Stack

| Layer | Technology |
|---|---|
| Core engine | Python (unchanged) |
| OCR | Tesseract (`pytesseract` + `Pillow`, `pdf2image`) |
| Backend API | Python **FastAPI** |
| Auth | **Supabase Auth** (Google OAuth provider) |
| Database | **Supabase** (Postgres) |
| File storage | **Supabase Storage** (for uploaded transcript images) |
| Web frontend | **Vite + React** |
| Mobile app | **Expo (React Native)** — fastest to ship, shares JS patterns with React |
| Web deploy | **Vercel** |
| API deploy | **Railway** or **Render** (free tier, Supabase-friendly) |
| Load testing | **Locust** |
| CI / quality | **ruff**, **black**, **mypy**, **pytest**, **GitHub Actions** |

---

## Final Architecture

```
GradGate-v2/
├── engine/                     ← UNTOUCHED Python audit core
├── api/                        ← NEW: FastAPI backend
│   ├── main.py                 ← app entry point
│   ├── routers/
│   │   ├── audit.py            ← POST /audit/csv, POST /audit/image
│   │   └── history.py          ← GET /history, GET /history/{id}
│   ├── services/
│   │   ├── ocr.py              ← Tesseract pipeline
│   │   └── supabase_client.py  ← Supabase admin client
│   ├── models.py               ← Pydantic schemas
│   └── auth.py                 ← JWT validation from Supabase
├── webapp/                     ← NEW: Vite + React
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Results.jsx
│   │   │   └── History.jsx
│   │   └── api/client.js       ← Supabase JS client + fetch to API
│   └── vite.config.js
├── mobile/                     ← NEW: Expo (React Native)
│   ├── app/
│   │   ├── (auth)/login.tsx
│   │   ├── (tabs)/index.tsx    ← Upload screen
│   │   ├── (tabs)/history.tsx
│   │   └── results.tsx
│   └── app.json
├── tests/
│   ├── ... (existing 57 tc*.csv files)
│   ├── test_ocr.py             ← OCR unit test
│   └── load/locustfile.py      ← concurrency tests
├── .github/workflows/ci.yml    ← GitHub Actions
├── pyproject.toml              ← deps + tool config
└── Makefile                    ← dev shortcuts
```

---

## Phase 1 — Repo Foundation & CI/CD Quality Pipeline

**Output:** A clean, lintable, testable repo that gates quality on every push.

### What to build

1. **`pyproject.toml`** — unified Python config
   ```toml
   [tool.ruff]    # linting
   [tool.black]   # formatting
   [tool.mypy]    # type checking
   [tool.pytest]  # test runner
   ```
2. **`Makefile`** with targets: `lint`, `format`, `typecheck`, [test](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/gradgate.py#294-331), `serve-api`
3. **`.github/workflows/ci.yml`** — on every push/PR:
   - `ruff check .`
   - `black --check .`
   - `mypy engine/ api/`
   - `pytest tests/ -x`
4. **`.pre-commit-config.yaml`** — hooks for local dev
5. Reorganize v2 folder: create `api/`, `webapp/`, `mobile/` stubs

### Dependencies added
```
ruff, black, mypy, pytest, pytest-cov, pre-commit
```

---

## Phase 2 — FastAPI Backend + Supabase + Google Auth

**Output:** A working REST API with auth, runs locally, connects to a live Supabase project.

### Supabase setup (one-time in dashboard)
- Create project `gradgate-v2`
- Enable **Google OAuth provider** in Auth → Providers
- Create tables:
  ```sql
  -- scan_sessions: one row per audit run
  create table scan_sessions (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid references auth.users(id),
    created_at  timestamptz default now(),
    program     text,
    input_type  text,          -- 'csv' | 'image'
    file_url    text,          -- Supabase Storage path
    result_json jsonb          -- full audit result
  );
  ```
- Create Supabase Storage bucket: `transcripts` (private)
- Set RLS on `scan_sessions`: users can only see their own rows

### API structure

**`api/main.py`**
```python
app = FastAPI()
app.include_router(audit.router, prefix="/audit")
app.include_router(history.router, prefix="/history")
```

**`api/auth.py`** — middleware that validates Supabase JWT from `Authorization: Bearer <token>` header

**`api/routers/audit.py`**
- `POST /audit/csv` — accepts multipart CSV file + [program](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/engine/program_loader.py#226-469) param → runs engine → saves to DB → returns JSON
- `POST /audit/image` — accepts image/PDF → OCR → CSV → engine → saves → returns JSON

**`api/routers/history.py`**
- `GET /history` — list user's past scans (id, created_at, program, input_type)
- `GET /history/{id}` — full result JSON for one scan

**`api/services/supabase_client.py`** — singleton `create_client(url, service_key)`

### Key design: engine integration
The existing engine functions are imported directly into the API:
```python
from engine.transcript import load_transcript, resolve_retakes
from engine.audit import run_audit
# etc.
```
No engine code is modified.

### Environment variables (`.env`)
```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_JWT_SECRET=
```

### Dependencies added
```
fastapi, uvicorn, python-multipart, supabase, python-dotenv, pydantic
```

---

## Phase 3 — OCR Transcript Scanner

**Output:** `api/services/ocr.py` — accepts an image or PDF, returns a transcript CSV string.

### Pipeline

```
Input file (PNG/JPEG/PDF)
   │
   ▼
pdf2image (if PDF → pages as PIL images)
   │
   ▼
Pillow preprocessing:
  - Convert to grayscale
  - Increase contrast (ImageEnhance)
  - Threshold (binarization)
   │
   ▼
pytesseract.image_to_string()
   │
   ▼
Regex parser: extract Course_Code, Credits, Grade, Semester
   │
   ▼
Returns: List[dict] or CSV string
```

### OCR parser logic
NSU transcripts have a consistent table format. The parser uses:
```python
# Matches lines like: "CSE115   3   A-   Summer 2023"
COURSE_PATTERN = re.compile(
    r'([A-Z]{2,4}\d{3}[A-Z]?)\s+(\d+(?:\.\d+)?)\s+'
    r'(A\+?|A-?|B[+-]?|C[+-]?|D[+-]?|F|W|I|T|P)\s+'
    r'(Spring|Summer|Fall)\s+(\d{4})'
)
```

### CLI extension
```bash
python gradgate.py --upload transcript.png CSE
# OCR → CSV → run audit (no API needed, runs locally)
```

### Dependencies added
```
pytesseract, Pillow, pdf2image
# System: brew install tesseract poppler
```

### Test
`tests/test_ocr.py` — uses a sample NSU-style transcript image, asserts the extracted CSV matches expected rows.

---

## Phase 4 — Web App (Vite + React)

**Output:** A deployed web app on Vercel with login, upload, results, and history.

### Setup
```bash
cd webapp && npm create vite@latest . -- --template react
npm install @supabase/supabase-js react-router-dom axios
```

### Pages / Routes

| Route | Component | Description |
|---|---|---|
| `/` | `Login.jsx` | Google Sign-In via `supabase.auth.signInWithOAuth` |
| `/dashboard` | `Dashboard.jsx` | File upload (CSV or image), program selector, submit button |
| `/results/:id` | `Results.jsx` | Display structured audit output (credit table, CGPA, audit report) |
| `/history` | `History.jsx` | List of past scans, click → re-open results |

### Auth flow
```js
// Login.jsx
supabase.auth.signInWithOAuth({ provider: 'google' })

// All API calls include the Supabase access token:
const { data: { session } } = await supabase.auth.getSession()
axios.post('/audit/csv', formData, {
  headers: { Authorization: `Bearer ${session.access_token}` }
})
```

### Deployment
- `vercel.json` with rewrites: API calls proxy to the FastAPI server URL
- `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` as Vercel env vars
- Deploy: `vercel --prod`

---

## Phase 5 — Mobile App (Expo / React Native)

**Output:** iOS/Android app installable via Expo Go for demo day.

### Setup
```bash
cd mobile && npx create-expo-app . --template blank-typescript
npx expo install @supabase/supabase-js expo-image-picker expo-document-picker
npm install @react-navigation/native @react-navigation/tabs
```

### Screens

| Screen | Description |
|---|---|
| `login.tsx` | Google Sign-In via `supabase.auth.signInWithOAuth` + WebBrowser |
| `index.tsx` (Upload) | Camera capture OR file picker → upload to API |
| `results.tsx` | Display audit result cards (credit summary, CGPA, grad status) |
| `history.tsx` | List of past scans |

### Camera → OCR flow
```tsx
// User taps "Scan Transcript"
const result = await ImagePicker.launchCameraAsync({ quality: 0.8 })
// Upload image to API
const formData = new FormData()
formData.append('file', { uri: result.uri, type: 'image/jpeg', name: 'transcript.jpg' })
await axios.post(`${API_URL}/audit/image`, formData, { headers: { Authorization: ... } })
```

### Testing (no build needed)
```bash
npx expo start   # scan QR code with Expo Go
```

---

## Phase 6 — Load Testing (20 Concurrent Users)

**Output:** Automated Locust test proving system handles 20 concurrent users.

### `tests/load/locustfile.py`

```python
class GradGateUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Use a pre-seeded test JWT (bypass real OAuth for load test)
        self.token = os.environ["TEST_JWT"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def run_csv_audit(self):
        with open("tests/tc01_cse_all_pass.csv", "rb") as f:
            self.client.post(
                "/audit/csv",
                files={"file": f},
                data={"program": "CSE"},
                headers=self.headers,
            )

    @task(1)
    def view_history(self):
        self.client.get("/history", headers=self.headers)
```

### Run command
```bash
locust -f tests/load/locustfile.py \
  --headless -u 20 -r 5 --run-time 60s \
  --host http://localhost:8000 \
  --html tests/load/report.html
```

### Pass criteria
- All requests: 0% failure rate
- p95 response time: < 5 seconds
- `/audit/csv`: p95 < 3s

---

## Execution Order

```
Phase 1 (CI baseline)  →  Phase 2 (API + Supabase + Auth)  →  Phase 3 (OCR)
                                         │
                               ┌─────────┴──────────┐
                               ▼                    ▼
                         Phase 4 (Web)       Phase 6 (Load)
                               │
                               ▼
                         Phase 5 (Mobile)
```

Phase 2 is the critical path — Phases 3, 4, 5, and 6 all depend on the API being up.

## Priority vs. Deadline

Given the **March 8 deadline**:

| Phase | Time Estimate | Priority |
|---|---|---|
| Phase 1 — CI/Quality | ~1–2h | 🟡 Set up early, run in background |
| Phase 2 — API + Auth | ~3–4h | 🔴 Critical path, do first |
| Phase 3 — OCR | ~2–3h | 🔴 Core new feature |
| Phase 4 — Web App | ~3–4h | 🟠 Main demo surface |
| Phase 6 — Load Tests | ~1h | 🟠 Quick after API is up |
| Phase 5 — Mobile | ~4–6h | 🔵 Stretch goal |
