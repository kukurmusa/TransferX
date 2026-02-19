# TransferX

## Local setup (venv)

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

Copy env vars:

```bash
cp .env.example .env  # Windows: copy .env.example .env
```

Run the dev server:

```bash
python src/manage.py migrate
python src/manage.py seed_demo
python src/manage.py runserver
```

## Documentation

- Developer setup: `docs/DEV_SETUP.md`
- Admin guide: `docs/ADMIN_GUIDE.md`
- User guide: `docs/USER_GUIDE.md`

## Docker Compose

```bash
docker compose up --build
```

## Lint and tests

```bash
ruff check .
ruff format .
pytest
```

## Tailwind UI

Local CSS build:

```bash
npm install
npm run dev:css
```

Docker CSS build:

```bash
docker compose up tailwind
```

The built CSS is served from `src/static/css/tailwind.css`.

UI components live in `src/templates/components/` and can be used with:

```django
{% include "components/button.html" with text="Create" href="/auctions/new/" variant="primary" size="md" %}
```

Phase UI-2 pages updated:
- Auction detail + bid ladder partials
- Players list + player form
- Auction create form
- My Club + Finance
- Login

After changing templates, rebuild CSS:

```bash
npm run build:css
```

## API-Football stats sync

Set API-SPORTS credentials in `.env`:

```bash
APISPORTS_KEY=your-key
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
```

Map players to vendor ids in the Django admin (`/admin/`) using `PlayerVendorMap`,
then run:

```bash
python src/manage.py sync_player_stats --season 2025 --league-id 39 --limit 10 --sleep-ms 250
```

Compute derived player form:

```bash
python src/manage.py compute_player_form --season 2025 --league-id 39 --window-games 5
```

Form score ranges 0-100 and blends average rating with goals+assists per 90 over the window.

Bulk import players by club name (creates local players and mappings):

```bash
python src/manage.py sync_team_players --season 2026 --league-id 39 --clubs "Manchester United,Manchester City" --sleep-ms 250
```

## World data sync (clubs/players)

If you already have duplicates, run dedupe before adding constraints:

```bash
python src/manage.py dedupe_world_data --apply
```

Sync a league (idempotent via vendor IDs):

```bash
python src/manage.py sync_world_league --season 2025 --league-id 39 --sleep-ms 250
```

Sync multiple leagues:

```bash
python src/manage.py sync_world_top5 --season 2025 --leagues "39,140,135,78,61" --sleep-ms 250
```

Compute world profiles:

```bash
python src/manage.py compute_world_player_profiles --season 2025 --league-id 39 --limit 500
python src/manage.py compute_world_club_profiles --season 2025 --league-id 39
```

## Auction mechanics (Milestone 3.1)

- Optional `reserve_price` and `min_increment` when creating auctions.
- Minimum increment applies after the first bid.
- Auctions auto-close opportunistically when read/written (no scheduler yet).

## Budgets and wages (Milestone 3.2)

- Clubs have transfer and weekly wage budgets.
- Bids reserve both transfer fee and wage; acceptance commits them.
- One active bid per buyer per auction; a new bid replaces the previous one and adjusts reservations.
- Finance summary available at `/accounts/finance/`.

## Milestone 4 operator tooling

- Rate limiting for bid/accept endpoints via `django-ratelimit` (LocMemCache in dev).
- Anti-sniping config in `.env`:
  - `TRANSFERX_ENABLE_ANTI_SNIPING`, `TRANSFERX_SNIPING_WINDOW_MINUTES`, `TRANSFERX_SNIPING_EXTEND_MINUTES`
- Commands:
  - `python src/manage.py reset_season --confirm YES`
  - `python src/manage.py import_players_csv --file path/to/players.csv --owner seller1`
  - `python src/manage.py import_vendor_maps_csv --file path/to/maps.csv`
- CSV export: `/auctions/<id>/bids.csv` (seller-only)
- Note: LocMemCache is per-process; use a shared cache (Redis/Memcached) in prod for rate limiting.

## Marketplace domain alignment (M5)

- Clubs are first-class organizations (see `ClubProfile` fields in admin).
- Players are either `CONTRACTED` (current_club set) or `FREE_AGENT` (current_club null).
- Contracts live in `players.Contract` and update player status automatically.
- Listings are separate from auctions and represent marketplace availability.

Normalize player status:

```bash
python src/manage.py normalize_player_status
```

Mark a player as free agent (admin):
- Clear `current_club` and save.

Create a contract (admin):
- Add a `Contract` row and set `is_active=True`.

Create listings (admin):
- Use the `Listing` admin to create transfer/loan/free-agent listings.

Auctions remain available as public bidding mode.

## Offers and negotiation (M6)

- Offers are private between clubs and support countering, acceptance, rejection, withdrawal, and expiry.
- Free agent offers are allowed but acceptance is blocked until player onboarding.

Key URLs:
- `/marketplace/offers/received/` (inbox)
- `/marketplace/offers/sent/`
- `/marketplace/offers/new/?player=<id>`
- `/marketplace/offers/free-agents/` (staff)

## Discovery and profiles (M7)

Directories and profiles:
- `/players/market/`
- `/players/market/<id>/`
- `/players/free-agents/`
- `/clubs/`
- `/clubs/<id>/`
- `/listings/`
- `/listings/<id>/`

Open to offers:
- `players.Player.open_to_offers` is currently set by admin/club.
- Only meaningful for free agents (current_club is null).

## Scouting workflow (M8)

Scouting URLs:
- `/scouting/targets/`
- `/scouting/shortlists/`
- `/scouting/shortlists/<id>/`

Key concepts:
- Shortlists can be created per club and hold players with priority and notes.
- Interests track level + stage per player.
- Targets dashboard shows recently updated items, expiring offers (next 72h), and watched players now available.
