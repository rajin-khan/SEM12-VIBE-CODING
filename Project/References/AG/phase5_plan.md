# Phase 5 — GradGate Mobile App (Expo + React Native)

**Output:** iOS app running on iPhone simulator (M1 Mac), matching the webapp's light mode design exactly.

---

## Design Parity

The mobile app mirrors the web design system:

| Token | Value |
|---|---|
| Background | `#FAF8F5` (warm parchment) |
| Foreground | `#1A1714` (ink) |
| Muted text | `#7A7267` |
| Surface/Card | `rgba(255,255,255,0.8)` with border `rgba(26,23,20,0.07)` |
| Display font | `Instrument_Serif` (from `@expo-google-fonts/instrument-serif`) |
| Body font | `DMSans_400Regular`, `DMSans_500Medium`, `DMSans_600SemiBold` |
| Border radius | `sm: 4px`, `card: 16px`, `pill: 99px` |
| Shadow | `shadowColor: #1A1714`, `shadowOpacity: 0.06`, `shadowRadius: 16` |

---

## Screens

| Screen | Route | Maps to Web |
|---|---|---|
| Login | `/(auth)/login` | [Login.jsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/pages/Login.jsx) |
| Upload | `/(tabs)/index` | [Dashboard.jsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/pages/Dashboard.jsx) |
| History | `/(tabs)/history` | [History.jsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/pages/History.jsx) |
| Results | `/results/[id]` | [Results.jsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/pages/Results.jsx) |
| Testing | `/(tabs)/testing` | [Testing.jsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/pages/Testing.jsx) |

---

## Step-by-Step Plan

### Step 1 — Scaffold

```bash
cd /Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2
npx create-expo-app mobile --template blank-typescript
cd mobile
```

### Step 2 — Install Dependencies

```bash
# Navigation
npx expo install expo-router expo-linking expo-constants expo-status-bar

# Auth & API
npx expo install @supabase/supabase-js
npx expo install expo-web-browser expo-auth-session

# File picking
npx expo install expo-image-picker expo-document-picker

# Fonts (matching webapp)
npx expo install @expo-google-fonts/instrument-serif @expo-google-fonts/dm-sans expo-font

# UI utilities
npx expo install expo-secure-store react-native-safe-area-context react-native-screens
```

### Step 3 — Configure `app.json`

```json
{
  "expo": {
    "name": "GradGate",
    "slug": "gradgate",
    "scheme": "gradgate",
    "plugins": ["expo-router", "expo-font"],
    "ios": { "bundleIdentifier": "com.gradgate.app" }
  }
}
```

### Step 4 — Design Tokens (`src/theme.ts`)

Single source of truth — mirrors [index.css](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/index.css):

```ts
export const colors = {
  background: '#FAF8F5',
  surface:    '#FFFFFF',
  foreground: '#1A1714',
  muted:      '#7A7267',
  stroke:     'rgba(26,23,20,0.07)',
}
export const fonts = {
  display: 'InstrumentSerif_400Regular',
  body:    'DMSans_400Regular',
  medium:  'DMSans_500Medium',
  semi:    'DMSans_600SemiBold',
}
export const radius = { sm: 4, md: 12, card: 16, pill: 99 }
```

### Step 5 — Shared Components (`src/components/`)

| Component | Description |
|---|---|
| `Card.tsx` | Glass-style card (white bg, soft shadow, ink border) |
| `PrimaryButton.tsx` | Ink-on-parchment, full-width, Instrument Serif label |
| `Label.tsx` | Uppercase tracking-wider muted label (section headers) |
| `StatusBadge.tsx` | ELIGIBLE (green) / DEFICIENT (red) pill |
| `LogoMark.tsx` | The two-bar + dot mark + "GradGate" in Instrument Serif |

### Step 6 — Auth (`src/lib/supabase.ts` + `src/lib/AuthContext.tsx`)

- Initialize `createClient` using `AsyncStorage`-backed session storage
- `AuthContext` exposes `session`, `loading`, `signOut()`
- Google OAuth via `supabase.auth.signInWithOAuth` + `expo-web-browser`

### Step 7 — Screens

#### [(auth)/login.tsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/lib/utils.js#4-7)
- Full-screen parchment background
- Centered `LogoMark` + tagline
- Google Sign-In button (Google G SVG + text, ink background)
- Redirect to `/(tabs)/` on success

#### [(tabs)/index.tsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/lib/utils.js#4-7) — Upload
- Section label: `NEW AUDIT`
- Display heading: `Upload Transcript` (Instrument Serif)
- Tap zone: rounded card with upload icon, file name preview
- Program picker: segmented control or styled picker (CSE/BBA/EEE/ETE)
- **Camera button** — opens `ImagePicker.launchCameraAsync`
- **File button** — opens `DocumentPicker.getDocumentAsync`
- Primary CTA: `Run Complete Degree Audit`
- Loading state with spinner

#### [(tabs)/history.tsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/lib/utils.js#4-7)
- Section label: `AUDIT HISTORY`  
- Display heading: `Past Scans`
- Skeleton loader while fetching
- List of `Card.tsx` rows: program, date, file name, arrow icon
- Empty state with `FileText` icon

#### `/results/[id].tsx`
- Large ELIGIBLE / DEFICIENT status at top
- Stats row: Credits (xx/120), CGPA
- Missing courses section (red-tinted cards)
- Academic Roadmap list
- Grade Distribution bar chart (using a simple RN-native bar)

#### [(tabs)/testing.tsx](file:///Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/webapp/src/lib/utils.js#4-7)
- Mirrors the web Testing page
- Multi-file picker (document picker, can pick multiple)
- Per-file row: filename, program selector, Run button, status icon
- Run All button at top
- View Results navigates to `/results/[id]`

### Step 8 — Tab Bar

```
[ Upload ]  [ History ]  [ Testing ]
```

Custom tab bar matching parchment theme:
- Background: `#FAF8F5` with top `1px` border in `rgba(26,23,20,0.07)`
- Active: ink `#1A1714`
- Inactive: muted `#7A7267`
- Phosphor-style icons via `@expo/vector-icons` Ionicons (similar thin weight)

### Step 9 — API Integration (`src/lib/api.ts`)

```ts
const API = process.env.EXPO_PUBLIC_API_URL  // e.g. http://192.168.x.x:8000
// All requests include: Authorization: Bearer <session.access_token>
```

> [!IMPORTANT]  
> For iPhone Simulator, the backend URL must be the **Mac's local network IP** (e.g. `192.168.1.x:8000`) — `localhost` does not work from the simulator.

### Step 10 — Run on Simulator

```bash
npx expo start --ios
# Selects iPhone 16 Pro by default
```

---

## Environment Variables

Create `mobile/.env`:
```
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000
EXPO_PUBLIC_SUPABASE_URL=<from webapp .env>
EXPO_PUBLIC_SUPABASE_ANON_KEY=<from webapp .env>
```

---

## File Structure

```
mobile/
├── app/
│   ├── (auth)/
│   │   └── login.tsx
│   ├── (tabs)/
│   │   ├── _layout.tsx       ← Tab bar config
│   │   ├── index.tsx         ← Upload
│   │   ├── history.tsx
│   │   └── testing.tsx
│   ├── results/
│   │   └── [id].tsx
│   └── _layout.tsx           ← Root layout, font loading, AuthContext
├── src/
│   ├── components/
│   │   ├── Card.tsx
│   │   ├── PrimaryButton.tsx
│   │   ├── Label.tsx
│   │   ├── StatusBadge.tsx
│   │   └── LogoMark.tsx
│   ├── lib/
│   │   ├── supabase.ts
│   │   ├── AuthContext.tsx
│   │   └── api.ts
│   └── theme.ts
├── .env
└── app.json
```

---

## Verification

- [ ] App boots on iPhone 16 Pro simulator
- [ ] Google OAuth opens Safari sheet and returns session
- [ ] CSV upload → runs audit → shows Results screen
- [ ] Camera capture → OCR audit → shows Results screen
- [ ] History lists past scans and navigates to Results
- [ ] Testing tab: batch upload, run all, view individual results
- [ ] All fonts (Instrument Serif + DM Sans) load correctly
- [ ] Design matches webapp: parchment bg, ink text, glass cards
