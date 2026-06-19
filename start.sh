#!/bin/sh
echo "=== STARTUP ==="
echo "DB: $([ -n "$DATABASE_URL" ] && echo YES || echo NO)"
echo "JWT: $([ -n "$JWT_SECRET_KEY" ] && echo YES || echo NO)"
echo "Backend dir: $(ls /app/backend/main.py 2>/dev/null && echo EXISTS || echo MISSING)"
cd /app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
cd /app
exec npm start
