# TransferX Developer Setup

Complete guide for setting up the local development environment, understanding the project layout, and running common workflows.

---

## Table of Contents

1. [Requirements](#1-requirements)
2. [Project layout](#2-project-layout)
3. [Local setup (venv)](#3-local-setup-venv)
4. [Environment variables](#4-environment-variables)
5. [Docker setup](#5-docker-setup)
6. [Tailwind CSS](#6-tailwind-css)
7. [Demo data](#7-demo-data)
8. [Running tests and lint](#8-running-tests-and-lint)
9. [Apps and responsibilities](#9-apps-and-responsibilities)
10. [Key patterns](#10-key-patterns)
11. [URL namespaces](#11-url-namespaces)
12. [HTMX conventions](#12-htmx-conventions)
13. [Template system](#13-template-system)
14. [Stats sync (API-Sports)](#14-stats-sync-api-sports)
15. [World data sync](#15-world-data-sync)
16. [Common issues](#16-common-issues)

---

## 1. Requirements

| Tool | Version |
|---|---|
| Python | 3.12 (3.11 acceptable) |
| Node.js | 20+ (for Tailwind build only) |
| PostgreSQL | 15+ |
| Docker Desktop | Optional (provides Postgres + Tailwind watch) |

---

## 2. Project layout

```
transferx/
├── src/
│   ├── config/
│   │   ├── settings/       # base.py, dev.py, prod.py
│   │   └── urls.py         # root URL config
│   ├── apps/
│   │   ├── accounts/       # users, clubs, finance, dashboard
│   │   ├── players/        # player roster, contracts
│   │   ├── auctions/       # public bidding engine
│   │   ├── marketplace/    # listings, direct offers
│   │   ├── deals/          # post-acceptance deal rooms
│   │   ├── scouting/       # shortlists, player interest
│   │   ├── stats/          # API-Sports sync, form scores
│   │   ├── world/          # real-world reference data
│   │   └── notifications/  # in-app notification centre
│   ├── templates/          # all templates (centralised)
│   │   ├── base.html       # sidebar layout, navbar
│   │   ├── components/     # reusable UI components
│   │   ├── dashboard/
│   │   ├── accounts/
│   │   ├── players/
│   │   ├── auctions/
│   │   ├── marketplace/
│   │   ├── deals/
│   │   ├── scouting/
│   │   ├── notifications/
│   │   └── world/
│   └── static/
│       └── css/
│           └── tailwind.css  # compiled output (do not edit by hand)
├── docs/                   # this directory
├── docker/                 # Dockerfile, entrypoint.sh
├── scripts/                # wait_for_db.py, etc.
├── tests/                  # pytest tests
├── pyproject.toml          # dependencies + ruff config
├── tailwind.config.js      # Tailwind v4 config
└── docker-compose.yml
```

---

## 3. Local setup (venv)

```bash
python -m venv .venv

# Linux / macOS:
. .venv/bin/activate

# Windows:
.venv\Scripts\activate

pip install -e .
```

Copy environment variables and edit as needed:

```bash
cp .env.example .env          # Linux/macOS
copy .env.example .env        # Windows
```

Apply migrations and seed demo data:

```bash
python src/manage.py migrate
python src/manage.py seed_demo
```

Start the dev server:

```bash
python src/manage.py runserver
```

In a separate terminal, start the Tailwind CSS watcher:

```bash
npm install
npm run dev:css
```

Visit `http://localhost:8000`. Log in with `seller1` / `buyer1` / `admin1` (all passwords: `password123`).

---

## 4. Environment variables

| Variable | Required | Description | Default |
|---|---|---|---|
| `SECRET_KEY` | Yes | Django secret key | — |
| `DEBUG` | No | Enable debug mode | `True` in dev |
| `DATABASE_URL` | No | Full Postgres URL | `localhost:5432/transferx` |
| `DB_NAME` | No | DB name (if not using DATABASE_URL) | `transferx` |
| `DB_USER` | No | DB user | `postgres` |
| `DB_PASSWORD` | No | DB password | `postgres` |
| `DB_HOST` | No | DB host | `localhost` |
| `DB_PORT` | No | DB port | `5432` |
| `APISPORTS_KEY` | No | API-Sports v3 key | — |
| `API_FOOTBALL_BASE_URL` | No | API base URL | `https://v3.football.api-sports.io` |
| `TRANSFERX_ENABLE_ANTI_SNIPING` | No | Extend auction deadline on last-minute bids | `False` |
| `TRANSFERX_SNIPING_WINDOW_MINUTES` | No | Minutes before deadline to trigger | `2` |
| `TRANSFERX_SNIPING_EXTEND_MINUTES` | No | Minutes to add | `2` |
| `TRANSFERX_BID_RATE` | No | Bid rate limit per user | `10/m` |

> In production, set `CACHES` to use Redis or Memcached so rate-limiting applies across all web processes. The default `LocMemCache` is per-process only.

---

## 5. Docker setup

Starts PostgreSQL, the Django web server, and the Tailwind watcher together:

```bash
docker compose up --build
```

> **Line endings warning:** `docker/web/entrypoint.sh` and `scripts/wait_for_db.py` must use **LF** line endings. CRLF causes `env: 'sh\r': No such file or directory` at container startup. Configure your editor or use `.gitattributes` to enforce this.

Run management commands inside the running container:

```bash
docker compose exec web python src/manage.py migrate
docker compose exec web python src/manage.py seed_demo
```

Run only the Tailwind watcher (if the web server is already running locally):

```bash
docker compose up tailwind
```

---

## 6. Tailwind CSS

TransferX uses **Tailwind CSS v4** with the `@tailwindcss/cli` build tool. All styles are compiled into `src/static/css/tailwind.css`.

**Do not edit `tailwind.css` directly.** It is regenerated on every build.

| Command | Purpose |
|---|---|
| `npm run dev:css` | Watch mode — rebuilds on template change |
| `npm run build:css` | One-off production build |
| `docker compose up tailwind` | Docker watch |

After changing templates (new classes, new components), always rebuild CSS. In CI, run `npm run build:css` before collecting static files.

### Design system

- **Color scheme:** dark, slate-based (`bg-slate-950` body, `bg-slate-900` cards)
- **Accent:** `emerald-500` / `emerald-400`
- **Borders:** `border-white/10`, card rounding `rounded-2xl`
- **Typography:** base `text-white`, secondary `text-slate-400`, muted `text-slate-500`

### Reusable components

Components live in `src/templates/components/`. Use `{% include %}` with `with` parameters:

```django
{% include "components/button.html" with text="Create" href="/auctions/new/" variant="primary" size="md" %}
{% include "components/badge.html" with text="Open" variant="emerald" %}
{% include "components/stat_card.html" with label="Squad size" value=squad_size %}
{% include "components/empty_state.html" with title="No players found" body="..." %}
{% include "components/page_header.html" %}
```

Available components: `badge`, `button`, `card`, `empty_state`, `sidebar_link`, `_sidebar_icon`, `page_header`, `stat_card`, `panel`, `metric`, `section_header`, `list_row`, `timeline`, `table`.

---

## 7. Demo data

`seed_demo` is idempotent — safe to run multiple times. It creates:

| Username | Password | Role | Club | Budget |
|---|---|---|---|---|
| `seller1` | `password123` | seller | Seller United | £200M transfer / £5M/wk wage |
| `buyer1` | `password123` | buyer | Buyer FC | £200M transfer / £5M/wk wage |
| `buyer2` | `password123` | buyer | Northside FC | £200M transfer / £5M/wk wage |
| `admin1` | `password123` | admin (staff, superuser) | Admin Town | £200M transfer / £5M/wk wage |

Groups: `buyer`, `seller`, `admin`. Role checks use `request.user.groups.filter(name="seller").exists()` (wrapped in helpers `is_seller()` / `is_buyer()` from `accounts.utils`).

---

## 8. Running tests and lint

```bash
# Lint
ruff check .

# Auto-fix lint issues
ruff check . --fix

# Format
ruff format .

# Tests (uses SQLite in-memory by default)
pytest

# Tests with coverage
pytest --cov=src --cov-report=term-missing
```

Tests live in `tests/`. Django test settings use SQLite for speed.

---

## 9. Apps and responsibilities

### `accounts`

- **Models:** `ClubProfile` (club metadata, crest, verified status), `ClubFinance` (transfer/wage budgets, reserved, committed)
- **Views:** `dashboard` (War Room), `finance_summary`, `my_club`
- **Utils:** `is_seller(user)`, `is_buyer(user)`, `get_or_create_finance_for_user(user)`
- **Context processors:** `deal_count_context` (IN_PROGRESS deal count for navbar badge)

### `players`

- **Models:** `Player` (name, age, position, nationality, status, visibility, photo_url, current_club, open_to_offers), `Contract` (active contract linking player to club with wage)
- **Services:** `normalize_player_market_flags(player)`, `create_contract(player, club, wage, ...)`
- **Helpers:** `player_search_queryset(request, queryset)` — applies filters from query params

### `auctions`

- **Models:** `Auction` (player, seller, deadline, reserve_price, min_increment, status), `Bid` (auction, buyer, amount, wage_offer_weekly, reserved funds, status), `AuctionEvent` (event_type, actor, payload)
- **Services:** `place_bid(auction, buyer, amount, wage)`, `accept_bid(auction, bid)`, `close_if_expired(auction)`, `get_best_bid_amount(auction)`, `get_minimum_next_bid(auction)`, `is_reserve_met(auction)`
- **Anti-sniping:** checked in `place_bid()` via `TRANSFERX_ENABLE_ANTI_SNIPING` setting

### `marketplace`

- **Models:** `Listing` (player, club, type, visibility, asking_price, deadline, status), `ListingInvite` (per-club invite for INVITE_ONLY listings), `Offer` (player, from_club, to_club, fee, wage, contract terms, status, expires_at), `OfferMessage`, `OfferEvent`
- **Services:** `create_draft_offer()`, `send_offer()`, `accept_offer()`, `counter_offer()`, `reject_offer()`, `withdraw_offer()`, `add_message()`, `close_offer_if_expired()`
- **Context processors:** `offer_unread_counts` (unread offer count for sidebar)

### `deals`

- **Models:** `Deal` (offer or auction → buyer_club, seller_club, player, agreed_fee, agreed_wage, status, stage), `DealNote`
- **Stage workflow (offer deals):** AGREEMENT → PAPERWORK → CONFIRMED → COMPLETED
- **Auction deals:** PENDING_COMPLETION → staff marks COMPLETED
- **Services:** stage advancement triggers `create_contract()` and updates `player.current_club` on COMPLETED

### `scouting`

- **Models:** `Shortlist` (club, name, description), `ShortlistItem` (shortlist, player, priority 1–5, notes), `PlayerInterest` (club, player, level, stage, notes)
- **Services:** `create_shortlist()`, `add_player_to_shortlist()`, `remove_player_from_shortlist()`, `set_player_interest()`, `clear_player_interest()`, `offers_expiring_soon(club)`, `watched_now_available(club)`

### `stats`

- **Models:** `PlayerStatsSnapshot` (raw API payload per player/season/league), `PlayerForm` (computed 0–100 score, trend, avg_rating, G+A), `PlayerStats` (seasonal aggregate), `VendorSyncState`
- **Form score:** blends average match rating (0–10 → 0–100) with goals + assists per 90 min over a rolling `window_games` (default 5)

### `world`

- **Models:** `WorldLeague`, `WorldClub` (vendor data for real clubs), `WorldPlayer`, `WorldSquadMembership`
- Separate from `players.Player` — world data is reference-only and not directly editable in the app

### `notifications`

- **Models:** `Notification` (recipient, type, message, link, is_read, related_player, related_club)
- **Context processors:** `notifications_unread_context` (unread count for bell icon)
- **Service:** `create_notification(recipient, type, message, link, related_player, related_club)`

---

## 10. Key patterns

### Role decorators

```python
from apps.accounts.decorators import seller_required, buyer_required

@seller_required
def my_view(request):
    ...
```

`@seller_required` redirects to login if user is not in the "seller" group. Same for `@buyer_required`.

### Club access

Never call `request.user.club_profile` directly — it raises `RelatedObjectDoesNotExist` if not set.

```python
club = getattr(request.user, "club_profile", None)
if club is None:
    # handle no-club case
```

### Finance

```python
from apps.accounts.finance import get_or_create_finance_for_user

finance = get_or_create_finance_for_user(request.user)
remaining = finance.transfer_remaining  # property: total − committed − reserved
```

### HTMX partial detection

```python
if request.htmx:
    return render(request, "marketplace/_player_market_grid.html", context)
return render(request, "marketplace/player_list.html", context)
```

### Humanize numbers in templates

```django
{% load humanize %}
{{ value|floatformat:0|intcomma }}
```

`django.contrib.humanize` is in `INSTALLED_APPS`.

---

## 11. URL namespaces

| Namespace | Prefix | Example |
|---|---|---|
| *(none)* | `/accounts/`, `/players/market/`, `/clubs/`, `/listings/` | `{% url 'login' %}` |
| `auctions:` | `/auctions/` | `{% url 'auctions:detail' pk %}` |
| `marketplace:` | `/marketplace/` | `{% url 'marketplace:offer_received' %}` |
| `scouting:` | `/scouting/` | `{% url 'scouting:targets_dashboard' %}` |
| `deals:` | `/deals/` | `{% url 'deals:detail' pk %}` |
| `notifications:` | `/notifications/` | `{% url 'notifications:list' %}` |
| `world:` | `/world/` | `{% url 'world:club_detail' pk %}` |

Discovery URLs (player market, club list, listing hub) have **no namespace** — they are included directly in the root URL config via `marketplace.discovery_urls`.

---

## 12. HTMX conventions

- **Middleware:** `HtmxMiddleware` from `django-htmx` adds `request.htmx` (truthy if request has `HX-Request` header).
- **Partial templates** are prefixed with `_` (e.g., `_player_market_grid.html`, `_active_auctions.html`).
- **URL updates:** use `hx-push-url="true"` on filter forms so filtered state is bookmarkable.
- **Polling:** `hx-trigger="every 15s"` on the dashboard auctions panel container.
- **Post-swap re-init:** listen for `htmx:afterSwap` in JS to re-initialise countdown timers after HTMX swaps content.

Example filter form:

```html
<form hx-get="{% url 'player_market_list' %}"
      hx-target="#player-grid"
      hx-push-url="true"
      hx-swap="innerHTML">
  ...
</form>
```

---

## 13. Template system

All templates are in `src/templates/`. The `DIRS` setting points to this directory.

### Base template (`base.html`)

Provides:
- Fixed left sidebar (collapsible, state saved in `localStorage`)
- Mobile hamburger + slide-in sidebar
- Notification bell with unread count (polled via HTMX)
- Deal badge in sidebar
- Main content area with responsive left margin
- `{% block content %}` for page content
- `{% block page_header %}`, `{% block page_title %}`, `{% block page_subtitle %}`, `{% block page_actions %}` blocks for page headers

### Sidebar state

The sidebar expands/collapses via JS. State is stored in `localStorage` key `transferx-sidebar-expanded`. When collapsed, `.sidebar-label` elements are hidden via the CSS rule `#sidebar[data-collapsed] .sidebar-label { display: none }`. The main content area shifts from `md:ml-16` (collapsed) to `md:ml-56` (expanded).

---

## 14. Stats sync (API-Sports)

Requires an API-Sports v3 subscription and `APISPORTS_KEY` in `.env`.

### Workflow

1. Add `PlayerVendorMap` records in Django admin (`/admin/stats/playervendormap/`) linking local `Player` records to API-Sports player IDs.
2. Sync raw stats:
   ```bash
   python src/manage.py sync_player_stats --season 2025 --league-id 39 --limit 50 --sleep-ms 250
   ```
3. Compute form scores:
   ```bash
   python src/manage.py compute_player_form --season 2025 --league-id 39 --window-games 5
   ```
4. Form scores (0–100) are stored in `PlayerForm` and displayed on player cards and profiles.

### Bulk team import

Import all players for a club (creates `Player` + `PlayerVendorMap` records):

```bash
python src/manage.py sync_team_players \
  --season 2026 --league-id 39 \
  --clubs "Arsenal,Chelsea" --sleep-ms 250
```

### Import vendor maps from CSV

```bash
python src/manage.py import_vendor_maps_csv --file maps.csv
```

CSV columns: `player_name`, `owner_username`, `vendor_player_id`, `vendor` (optional, default `api_sports_v3`).

---

## 15. World data sync

World data (real leagues, clubs, and players) is stored in the `world` app and used as reference data. It is separate from the editable `players.Player` records.

```bash
# Deduplicate before adding constraints (only needed once if duplicates exist)
python src/manage.py dedupe_world_data --apply

# Sync a single league
python src/manage.py sync_world_league --season 2025 --league-id 39 --sleep-ms 250

# Sync all top-5 leagues at once
python src/manage.py sync_world_top5 --season 2025 --leagues "39,140,135,78,61" --sleep-ms 250

# Compute derived profiles
python src/manage.py compute_world_player_profiles --season 2025 --league-id 39 --limit 500
python src/manage.py compute_world_club_profiles --season 2025 --league-id 39
```

Common league IDs: `39` Premier League · `140` La Liga · `135` Serie A · `78` Bundesliga · `61` Ligue 1.

---

## 16. Common issues

| Problem | Cause | Fix |
|---|---|---|
| CSS not applying | Tailwind not watching / not built | Run `npm run dev:css` or `npm run build:css`, then hard refresh |
| DB connection error | Postgres not running / wrong credentials | Check Postgres is up; verify `DB_HOST`, `DB_PORT`, `DB_PASSWORD` in `.env` |
| Container fails on startup: `env: 'sh\r': No such file or directory` | CRLF line endings in `entrypoint.sh` | Convert to LF: `dos2unix docker/web/entrypoint.sh` |
| Rate limit errors in dev | Multiple fast bids in manual testing | Increase `TRANSFERX_BID_RATE` in `.env` (e.g., `100/m`) |
| `RelatedObjectDoesNotExist` on `club_profile` | User has no club | Use `getattr(request.user, "club_profile", None)` pattern |
| HTMX partial not rendering | `request.htmx` is False | Ensure `HtmxMiddleware` is in `MIDDLEWARE` and `django-htmx` is installed |
| Form score missing on player cards | Stats not synced or form not computed | Run `sync_player_stats` then `compute_player_form` |
