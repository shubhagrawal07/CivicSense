# CivicSense frontend

React + TypeScript (Vite) app for citizens to report civic issues and track their status.

## Setup

```bash
cp .env.example .env
npm install
npm run dev
```

Login and register always use the real backend, so it must be running (see the root README) with `FRONTEND_ORIGIN` left at `http://localhost:5173`. Reports run against a built-in mock API by default (`VITE_USE_MOCK_API=true`), so the submit → analysing → result flow works without SL-11 or SL-16. Set it to `false` and point `VITE_API_BASE_URL` at the real backend to use the real report API.

## Auth

`AuthProvider` (`src/auth/AuthContext.tsx`) exposes `{user, token, login(), logout(), isLoading, isAuthenticated}`. On load it calls `GET /auth/me` with the stored token, and a failed call logs the user out. `ProtectedRoute` shows a spinner while that check runs and then either renders the page or redirects to `/login`, remembering where the user was going. Any 401 on a request that carried a token logs the user out.

The token is kept in `localStorage` under `authToken`. That is simple, but any script that runs on the page (an XSS bug or a compromised dependency) can read it. Moving to an httpOnly cookie is the Sprint 2 hardening option; it needs backend changes (cookie, CSRF protection, CORS with credentials).

After login the user goes to the page they were trying to reach, or to `/my-reports`, which is a placeholder until SL-27.

## Scripts

- `npm run dev` — local dev server
- `npm run build` — type-check and production build
- `npm run lint` — ESLint
- `npm run test` — Vitest component/hook tests

## Manual test checklist

Covers flows not exercised by the automated tests (Leaflet map interaction, full page navigation), per the SL-15 acceptance criteria. Run with `VITE_USE_MOCK_API=true`.

- [ ] `/report/new` renders the form after logging in.
- [ ] Submitting with neither description nor photo is blocked with an inline message.
- [ ] Clicking the map in `LocationPicker` drops a pin; "use my current location" requests geolocation (and degrades gracefully if denied).
- [ ] Uploading a non-JPEG/PNG file, or one over 5MB, shows an inline error and does not attach the file.
- [ ] Submitting with a description only succeeds and shows the confirmation screen with a report id.
- [ ] From the confirmation screen, "View this report" navigates to `/reports/:id`.
- [ ] `/reports/:id` shows an "Analysing" state, then auto-updates to the result card within ~6 seconds (no manual refresh).
- [ ] Submitting a description containing the word "fail" results in a FAILED report with a visible error message.
- [ ] Visiting an unknown route shows the not-found page instead of crashing.

## Manual test checklist: auth (SL-24)

Needs the backend running and migrated.

- [ ] Visiting `/report/new` while logged out redirects to `/login`.
- [ ] Registering with a short password or a bad email shows an error under that field, without calling the server.
- [ ] Registering an email that already exists shows "Email already registered" under the email field.
- [ ] A new registration logs the user in and lands on the page they wanted (`/report/new`), or `/my-reports` if they came straight to `/register`.
- [ ] Logging in with a wrong password shows "Incorrect email or password" and stays on the page.
- [ ] After login, the header shows the user's name and a Log out button. Refreshing the page keeps the user logged in.
- [ ] Log out clears the session; going back to a protected page redirects to `/login`.
- [ ] Deleting or corrupting `authToken` in DevTools and refreshing sends the user to `/login`.
- [ ] While logged in, `/login` and `/register` redirect away.
