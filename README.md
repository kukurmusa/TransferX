# TransferX

A football player transfer marketplace platform built with Django, HTMX, and Tailwind CSS v4. Clubs negotiate player deals via auctions and direct offers, track scouting targets, and manage squad finances — all in real time.

---

## Table of Contents

- [Architecture overview](#architecture-overview)
- [Quick start (local venv)](#quick-start-local-venv)
- [Docker setup](#docker-setup)
- [Tailwind CSS build](#tailwind-css-build)
- [Environment variables](#environment-variables)
- [Demo accounts](#demo-accounts)
- [Management commands](#management-commands)
- [Stats sync (API-Sports)](#stats-sync-api-sports)
- [World data sync](#world-data-sync)
- [Lint and tests](#lint-and-tests)
- [Documentation](#documentation)

---

## Architecture overview

| Layer | Tech |
|---|---|
| Backend | Django 5.x, Python 3.12 |
| Frontend | HTMX 2.x, Tailwind CSS v4 |
| Database | PostgreSQL (SQLite for tests) |
| Auth | Django sessions, group-based roles |
| Real-time | HTMX polling + JS countdown timers |

### Apps

| App | Responsibility |
|---|---|
| `accounts` | Users, ClubProfile, ClubFinance, dashboard |
| `players` | Player roster, contracts, free-agent status |
| `auctions` | Public bidding on players with deadline + reserve |
| `marketplace` | Listings, direct offers, offer negotiation |
| `deals` | Deal rooms (post-acceptance contract stages) |
| `scouting` | Shortlists, player interest tracking, targets dashboard |
| `stats` | API-Sports stats snapshots, player form scores |
| `world` | Real-world league/club/player reference data |
| `notifications` | In-app notification centre |

### Key URL namespaces

| Namespace | Prefix |
|---|---|
| *(no namespace)* | `/`, `/accounts/`, `/players/market/`, `/clubs/`, `/listings/` |
| `auctions:` | `/auctions/` |
| `marketplace:` | `/marketplace/` |
| `scouting:` | `/scouting/` |
| `deals:` | `/deals/` |
| `notifications:` | `/notifications/` |
| `world:` | `/world/` |

---

## Quick start (local venv)

```bash
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -e .
```

Copy environment variables:

```bash
cp .env.example .env          # Linux/macOS
copy .env.example .env        # Windows
```

Run migrations, seed demo data, and start:

```bash
python src/manage.py migrate
python src/manage.py seed_demo
python src/manage.py runserver
```

Visit `http://localhost:8000` and log in with a demo account (see [Demo accounts](#demo-accounts)).

---

## Docker setup

```bash
docker compose up --build
```

> **Note:** `docker/web/entrypoint.sh` and `scripts/wait_for_db.py` must have **LF** line endings (not CRLF) or the container will fail to start with `env: 'sh\r': No such file or directory`.

---

## Tailwind CSS build

The built CSS is served from `src/static/css/tailwind.css`. Rebuild after changing templates.

**Local watch (recommended for development):**

```bash
npm install
npm run dev:css
```

**One-off build:**

```bash
npm run build:css
```

**Docker watch:**

```bash
docker compose up tailwind
```

---

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | *(required)* |
| `DATABASE_URL` | Postgres connection string | `localhost:5432` |
| `APISPORTS_KEY` | API-Sports v3 API key | *(optional)* |
| `API_FOOTBALL_BASE_URL` | API-Sports base URL | `https://v3.football.api-sports.io` |
| `TRANSFERX_ENABLE_ANTI_SNIPING` | Extend deadline on last-minute bids | `False` |
| `TRANSFERX_SNIPING_WINDOW_MINUTES` | Minutes before deadline to trigger anti-sniping | `2` |
| `TRANSFERX_SNIPING_EXTEND_MINUTES` | Minutes to add when anti-sniping fires | `2` |
| `TRANSFERX_BID_RATE` | Bid rate limit per user | `10/m` |

> Rate limiting uses `LocMemCache` in dev. For production, configure a shared cache (Redis/Memcached) so limits apply across all processes.

---

## Demo accounts

Created by `python src/manage.py seed_demo`. All passwords are `password123`.

| Username | Role | Club |
|---|---|---|
| `seller1` | Seller | Seller United |
| `buyer1` | Buyer | Buyer FC |
| `buyer2` | Buyer | Northside FC |
| `admin1` | Admin (staff + superuser) | Admin Town |

Roles:
- **Seller** — creates players, auctions, and listings.
- **Buyer** — places bids and makes direct offers.
- **Admin** — full Django admin access; can manage all data and complete/collapse deals.

---

## Management commands

### Season operations

```bash
# Seed demo users, clubs, and finance balances
python src/manage.py seed_demo

# Reset season: deletes auctions, bids, events, snapshots, form scores
# (keeps users, clubs, players, and vendor maps)
python src/manage.py reset_season --confirm YES

# Normalize player status (CONTRACTED vs FREE_AGENT) from current_club field
python src/manage.py normalize_player_status
```

### Player import

```bash
# Import players from CSV (columns: name, age, position, valuation)
python src/manage.py import_players_csv --file path/to/players.csv --owner seller1

# Import vendor ID mappings from CSV
# (columns: player_name, owner_username, vendor_player_id, vendor)
python src/manage.py import_vendor_maps_csv --file path/to/maps.csv
```

### Anti-sniping / config

Anti-sniping settings are read from `.env` at runtime. No command needed — set the environment variables and restart.

---

## Stats sync (API-Sports)

Requires `APISPORTS_KEY` in `.env`.

```bash
# Sync raw stats snapshots (up to --limit players, throttled by --sleep-ms)
python src/manage.py sync_player_stats --season 2025 --league-id 39 --limit 10 --sleep-ms 250

# Compute form scores (0–100) from recent snapshots over a rolling window
python src/manage.py compute_player_form --season 2025 --league-id 39 --window-games 5

# Bulk import a team's players from the API and create local Player records
python src/manage.py sync_team_players \
  --season 2026 --league-id 39 \
  --clubs "Manchester United,Manchester City" --sleep-ms 250
```

Form score (0–100) blends average match rating with goals + assists per 90 minutes over the window.

---

## World data sync

World data (real leagues, clubs, players) is stored separately from the app's editable players.

```bash
# Remove duplicate world records before applying constraints
python src/manage.py dedupe_world_data --apply

# Sync a single league (idempotent via vendor IDs)
python src/manage.py sync_world_league --season 2025 --league-id 39 --sleep-ms 250

# Sync multiple leagues at once
python src/manage.py sync_world_top5 --season 2025 --leagues "39,140,135,78,61" --sleep-ms 250

# Compute derived profiles for world players/clubs
python src/manage.py compute_world_player_profiles --season 2025 --league-id 39 --limit 500
python src/manage.py compute_world_club_profiles --season 2025 --league-id 39
```

Common league IDs: `39` (Premier League), `140` (La Liga), `135` (Serie A), `78` (Bundesliga), `61` (Ligue 1).

---

## Lint and tests

```bash
ruff check .
ruff format .
pytest
```

---

## Documentation

| Document | Contents |
|---|---|
| `docs/USER_GUIDE.md` | Full end-to-end user guide: roles, dashboard, marketplace, auctions, offers, deals, scouting, finance |
| `docs/DEV_SETUP.md` | Developer environment setup, build pipeline, common issues |
| `docs/ADMIN_GUIDE.md` | Django admin operations, bulk imports, season management, rate limits |
