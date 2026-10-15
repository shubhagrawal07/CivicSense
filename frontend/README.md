# CivicSense frontend

React + TypeScript (Vite) app for citizens to report civic issues and track their status.

## Setup

```bash
cp .env.example .env
npm install
npm run dev
```

Runs against a built-in mock API by default (`VITE_USE_MOCK_API=true`), so the full submit → analysing → result flow works with no backend running. Set it to `false` and point `VITE_API_BASE_URL` at the real backend once SL-11 is available.

## Scripts

- `npm run dev` — local dev server
- `npm run build` — type-check and production build
- `npm run lint` — ESLint
- `npm run test` — Vitest component/hook tests

## Manual test checklist

Covers flows not exercised by the automated tests (Leaflet map interaction, full page navigation), per the SL-15 acceptance criteria. Run with `VITE_USE_MOCK_API=true`.

- [ ] `/report/new` renders the form (through the dev auth stub).
- [ ] Submitting with neither description nor photo is blocked with an inline message.
- [ ] Clicking the map in `LocationPicker` drops a pin; "use my current location" requests geolocation (and degrades gracefully if denied).
- [ ] Uploading a non-JPEG/PNG file, or one over 5MB, shows an inline error and does not attach the file.
- [ ] Submitting with a description only succeeds and shows the confirmation screen with a report id.
- [ ] From the confirmation screen, "View this report" navigates to `/reports/:id`.
- [ ] `/reports/:id` shows an "Analysing" state, then auto-updates to the result card within ~6 seconds (no manual refresh).
- [ ] Submitting a description containing the word "fail" results in a FAILED report with a visible error message.
- [ ] Visiting an unknown route shows the not-found page instead of crashing.
