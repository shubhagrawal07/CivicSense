# CivicSense

A civic issue reporting platform. Citizens report a problem with a description, a photo and a location, and the backend works out what it is, how serious it looks, whether it has already been reported, and who is responsible for fixing it.


## How it works

A **Report** is one citizen's submission. An **Issue** is the real-world problem behind it, and many reports can point to the same issue.

When a report comes in, the backend:

1. Classifies it from the description, the photo, or both. If they disagree, the photo takes priority.
2. Estimates how severe it is.
3. Links it to an existing nearby issue, or creates a new one.
4. Finds the responsible department and its official contact details.

Submitting a report returns straight away. The analysis runs in the background, and the report updates once it finishes.

## Tech stack

| Area | Choice |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Database | PostgreSQL + PostGIS (in Docker), SQLAlchemy with GeoAlchemy2, Alembic |
| Auth | Argon2 password hashing, JWT, roles: citizen, officer, admin |
| Background work | FastAPI `BackgroundTasks`. The pipeline is a plain function, so it can move to a queue later |
| Text ML | scikit-learn: TF-IDF + Logistic Regression |
| Image ML | PyTorch / torchvision with a small pretrained model (MobileNetV3 or ResNet18), fine-tuned, CPU only. Pillow for image handling |
| Duplicate matching | Category, text similarity and PostGIS distance (`ST_DWithin`) |
| Scraper (Sprint 2) | Scrapy, BeautifulSoup, Playwright. Respects robots.txt and rate limits, and stores the source URL and last-verified date for every contact |
| Frontend | React + TypeScript (Vite), React Router, Recharts |
| Maps | Leaflet + OpenStreetMap |
| File storage | Local `uploads/` folder, served as static files |
| Testing and quality | pytest, ruff, black |
| Dev setup | Docker for the database only. Backend and frontend run locally |
| Tracking and docs | Git + GitHub, Jira, Confluence |

## Project structure

```
civicsense/
├── backend/
│   ├── app/
│   │   ├── api/            routes
│   │   ├── models/         database tables
│   │   ├── schemas/        request and response shapes
│   │   ├── services/       business logic and the processing pipeline
│   │   ├── intelligence/   loads trained models and serves predictions
│   │   └── core/           config, security, database session
│   ├── migrations/
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       └── pages/
├── ml/                     offline training: datasets, scripts, saved models
├── uploads/                user photos (not in git)
└── docs/                   design doc, flows, API contract, decisions
```

`ml/` is where models are trained and evaluated. `backend/app/intelligence/` only loads the finished models and uses them when a report is processed.

