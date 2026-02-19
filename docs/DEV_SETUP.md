# TransferX Developer Setup

This guide covers local development, Docker, and common workflows. Update this file after any major project change.

## Requirements

- Python 3.12 (3.11 acceptable)
- Node.js 20+ (for Tailwind build)
- Docker Desktop (optional, for Postgres + Tailwind watch)

## Local setup (venv)

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

Copy environment variables:

```bash
cp .env.example .env  # Windows: copy .env.example .env
```

Run migrations and seed demo users:

```bash
python src/manage.py migrate
python src/manage.py seed_demo
```

Run the dev server:

```bash
python src/manage.py runserver
```

## Docker setup

```bash
docker compose up --build
```

## Tailwind CSS build

Local watch:

```bash
npm install
npm run dev:css
```

Docker watch:

```bash
docker compose up tailwind
```

Build once:

```bash
npm run build:css
```

## Lint and tests

```bash
ruff check .
ruff format .
pytest
```

## Stats sync (API-Sports v3)

Set credentials in `.env`:

```bash
APISPORTS_KEY=your-key
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
```

Sync player stats:

```bash
python src/manage.py sync_player_stats --season 2025 --league-id 39 --limit 10 --sleep-ms 250
```

Compute form score:

```bash
python src/manage.py compute_player_form --season 2025 --league-id 39 --window-games 5
```

## World data sync (clubs/players)

If duplicates exist, run dedupe before applying constraints:

```bash
python src/manage.py dedupe_world_data --apply
```

Sync a league:

```bash
python src/manage.py sync_world_league --season 2025 --league-id 39 --sleep-ms 250
```

Sync multiple leagues:

```bash
python src/manage.py sync_world_top5 --season 2025 --leagues "39,140,135,78,61" --sleep-ms 250
```

## Common issues

- CSS not applying: run `npm run dev:css` or `npm run build:css` and refresh.
- DB connection errors: ensure Postgres is running and `.env` matches your local DB.

## Maintenance

Update this file after any major workflow, dependency, or build change.

## Marketplace (M5)

- Player status: `CONTRACTED` if current club set; otherwise `FREE_AGENT`.
- Normalize status if needed:

```bash
python src/manage.py normalize_player_status
```

## Scouting workflow (M8)

Scouting is a first-class app:
- Shortlists, interests, and a targets dashboard.
- URLs: `/scouting/shortlists/` and `/scouting/targets/`.

No additional setup required beyond running migrations.
