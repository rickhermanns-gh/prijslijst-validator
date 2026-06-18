#!/bin/sh
# Startup script voor Railway — start beide services met zichtbare logs

echo "=== STARTUP CHECK ==="
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo YES || echo NO)"
echo "JWT_SECRET_KEY set: $([ -n "$JWT_SECRET_KEY" ] && echo YES || echo NO)"
echo "Python: $(python --version 2>&1)"
echo "Working dir: $(pwd)"
echo "Backend dir exists: $([ -d /app/backend ] && echo YES || echo NO)"
echo "===================="

# Start uvicorn vanuit de backend directory
echo "Starting uvicorn..."
cd /app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
echo "Uvicorn PID: $UVICORN_PID"

# Wacht even zodat uvicorn eventuele fouten kan loggen
sleep 2

# Check of uvicorn nog draait
if kill -0 $UVICORN_PID 2>/dev/null; then
    echo "✅ Uvicorn running"
else
    echo "❌ Uvicorn crashed! Exit code: $?"
fi

# Start Next.js in foreground (houdt container alive)
cd /app
exec npm start
