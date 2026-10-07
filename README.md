Project structure:

civicsense/
├── README.md
├── .gitignore
├── docker-compose.yml        # database only
├── .env.example
│
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── api/              # routes
│   │   ├── models/           # database tables
│   │   ├── schemas/          # request/response shapes
│   │   ├── services/         # business logic and pipeline
│   │   ├── intelligence/     # ML inference code
│   │   └── core/             # config, security, db
│   ├── migrations/
│   └── tests/
│
├── frontend/                 # React + TypeScript
│   └── src/
│       ├── api/
│       ├── components/
│       └── pages/
│
├── ml/                       # training, datasets, saved models
├── uploads/                  # user photos (not in git)
└── docs/                     # design doc, API contract, decisions