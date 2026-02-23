#!/bin/bash
set -e
echo "=== Starting TransferX ==="
echo "=== Working directory: $(pwd) ==="
echo "=== Python path: $(which python) ==="
cd /app
echo "=== Collecting static files ==="
python src/manage.py collectstatic --noinput
echo "=== Running migrations ==="
python src/manage.py migrate
echo "=== Seeding demo users ==="
python src/manage.py seed_demo
echo "=== Resetting demo passwords ==="
python src/manage.py reset_demo_passwords
echo "=== Checking player data ==="
PLAYER_COUNT=$(python src/manage.py shell -c "from apps.players.models import Player; print(Player.objects.count())" 2>/dev/null || echo "0")
if [ "${PLAYER_COUNT}" = "0" ]; then
    echo "=== No players found — syncing Premier League 2025 data ==="
    python src/manage.py sync_world_league --league-id 39 --season 2025 || echo "=== Warning: sync_world_league failed — skipping ==="
    python src/manage.py compute_player_form --season 2025 --league-id 39 || echo "=== Warning: compute_player_form failed — skipping ==="
    python src/manage.py normalize_player_status || echo "=== Warning: normalize_player_status failed — skipping ==="
else
    echo "=== Found ${PLAYER_COUNT} players — skipping sync ==="
fi
echo "=== Starting gunicorn ==="
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --chdir src
