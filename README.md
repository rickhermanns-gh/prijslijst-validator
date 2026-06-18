# Prijslijst Validator

> Interactieve web app voor 100% complete pricelist extraction uit PDFs  
> Gebouwd voor ai-werkers | 2026

## Wat doet dit?

Een end-to-end tool voor het valideren en verrijken van leveranciers-prijslijsten:

1. **Upload PDF** — ondersteunt Zimmer+Rohde, Eijffinger, Artex, etc.
2. **Scan 1** — Automatische extraction (pricing + specs)
3. **Gap Analysis** — Toon wat ontbreekt
4. **Scan 2** — Geavanceerde pattern matching
5. **Manual Validation** — Gebruiker vult ontbrekende specs in (pagina/kolom/cel reference)
6. **Export** — 100% complete CSV voor BMS import

## Stack

- **Frontend:** Next.js 14 + Tailwind CSS + Futura
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL op Railway
- **Auth:** Credentials + Microsoft SSO (toekomstig)
- **Deployment:** Railway

## Lokaal draaien

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL 14+

### Setup

```bash
# Clone & install dependencies
npm install
pip install -r requirements.txt

# Database setup
createdb prijslijst_dev
psql -U postgres -d prijslijst_dev < database/schema.sql

# Environment
cp .env.example .env.local
# Edit .env.local met je lokale database credentials
```

### Development

Terminal 1 — Frontend:
```bash
npm run dev
# http://localhost:3000
```

Terminal 2 — Backend:
```bash
uvicorn backend.main:app --reload
# http://localhost:8000/docs (API docs)
```

## Environment Variables

`.env.local` (nooit in git, zie `.env.example`):
```
DATABASE_URL=postgresql://user:password@localhost/prijslijst_dev
NEXTAUTH_SECRET=your-random-secret-here
NEXTAUTH_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

Railway environment variables (Bart zet dit in):
- DATABASE_URL
- NEXTAUTH_SECRET
- NEXTAUTH_URL (production URL)
- NEXT_PUBLIC_GA_MEASUREMENT_ID (optioneel)

## Deployment

Bart pusht naar Railway. App draait op:
```
https://prijslijst-validator.railway.app
```

## API Endpoints

- `POST /api/upload` — PDF upload + metadata
- `POST /api/scan1` — Scan 1: automatische extraction
- `GET /api/gap-analysis/{session_id}` — Gap analysis result
- `POST /api/scan2` — Scan 2: geavanceerde patterns
- `POST /api/validate/{session_id}` — Submit manual validation
- `GET /api/export/{session_id}` — Export CSV

Zie `docs/API.md` voor details.

## Database Schema

- `users` — login credentials
- `upload_sessions` — PDF processing sessions
- `validation_items` — ontbrekende specs per item
- `audit_log` — wie deed wat wanneer

Zie `database/schema.sql`.

## Changelog

Zie `docs/CHANGELOG.md`

---

**Contact:** Rick Hermanns (rickhermanns@gmail.com)
