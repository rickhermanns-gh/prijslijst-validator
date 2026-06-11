# Quick Start — Prijslijst Validator

## Setup (5 minuten)

### 1. Database
```bash
createdb prijslijst_dev
psql -U postgres -d prijslijst_dev < database/schema.sql
```

### 2. Environment
```bash
cp .env.example .env.local
# Edit .env.local met je database credentials
```

### 3. Install Dependencies
```bash
npm install
pip install -r requirements.txt
```

## Development (start beide servers)

### Terminal 1 — Frontend
```bash
npm run dev
```
→ http://localhost:3000

### Terminal 2 — Backend
```bash
cd backend
uvicorn main:app --reload
```
→ http://localhost:8000/docs

## Login
- **Username:** `demo`
- **Password:** `demo`

## Test Flow
1. Go to http://localhost:3000
2. Login
3. Select supplier "ZR" and upload a PDF
4. Watch Scan 1 → Gap Analysis → Scan 2 process
5. Validate missing items manually
6. Export 100% complete CSV

## Next Steps

### Backend
- [ ] Integrate actual PDF extraction (use existing Python scripts)
- [ ] Database queries (SQLAlchemy models)
- [ ] JWT authentication (FastAPI + python-jose)
- [ ] File handling & cleanup

### Frontend
- [ ] Scan 1 progress page
- [ ] Gap analysis dashboard
- [ ] Manual validation UI (item per item)
- [ ] Export & download
- [ ] Session state management (Zustand)

### Deployment
- [ ] Railway setup (Bart)
- [ ] Environment variables
- [ ] Database migration
- [ ] Health checks

## File Structure
```
PLHF/
├── app/              ← Next.js pages/routes
├── backend/          ← FastAPI routes & services
├── database/         ← SQL schemas
├── styles/           ← Global CSS + Tailwind
├── docs/             ← Documentation
└── ...config files
```

## API Endpoints
- `POST /api/auth/login` — Login
- `POST /api/upload` — Upload PDF
- `POST /api/scan1/{session_id}` — Start Scan 1
- `GET /api/gap-analysis/{session_id}` — Get gaps
- `POST /api/scan2/{session_id}` — Start Scan 2
- `POST /api/validate/{session_id}` — Submit validation
- `GET /api/export/{session_id}` — Export CSV

---

**Questions?** Check README.md or ask in development.
