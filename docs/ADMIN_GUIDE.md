# TransferX Admin Guide

Operational guide for managing a running TransferX instance. Covers the Django admin, management commands, season management, data imports, and production considerations.

---

## Table of Contents

1. [Accessing the admin panel](#1-accessing-the-admin-panel)
2. [Admin sections reference](#2-admin-sections-reference)
3. [User and club management](#3-user-and-club-management)
4. [Finance management](#4-finance-management)
5. [Player management](#5-player-management)
6. [Listings and auctions](#6-listings-and-auctions)
7. [Offers and deals](#7-offers-and-deals)
8. [Scouting oversight](#8-scouting-oversight)
9. [Stats and form scores](#9-stats-and-form-scores)
10. [World data](#10-world-data)
11. [Completing and collapsing deals (staff workflow)](#11-completing-and-collapsing-deals-staff-workflow)
12. [Season management](#12-season-management)
13. [Bulk imports](#13-bulk-imports)
14. [Notifications](#14-notifications)
15. [Rate limiting](#15-rate-limiting)
16. [Anti-sniping configuration](#16-anti-sniping-configuration)
17. [Production checklist](#17-production-checklist)

---

## 1. Accessing the admin panel

**URL:** `/admin/`

Log in with a staff account. The `seed_demo` command creates `admin1` (password: `password123`) as a staff and superuser account.

To grant staff access to an existing user:

1. Open `/admin/auth/user/<id>/change/`.
2. Check **Staff status**.
3. For superuser access (all permissions), also check **Superuser status**.
4. Save.

---

## 2. Admin sections reference

| Section | Model | Purpose |
|---|---|---|
| **Accounts** | `ClubProfile` | Club metadata (name, city, league, crest URL, vendor ID, verified status) |
| **Accounts** | `ClubFinance` | Budget totals and reserved/committed balances per club |
| **Players** | `Player` | Player master records (name, position, age, nationality, status, club, visibility) |
| **Players** | `Contract` | Active contracts (player ↔ club, wage, dates, release clause) |
| **Marketplace** | `Listing` | Transfer/loan/free-agent listings |
| **Marketplace** | `ListingInvite` | Per-club invites for INVITE_ONLY listings |
| **Marketplace** | `Offer` | Direct offer negotiation records |
| **Marketplace** | `OfferMessage` | Messages within an offer thread |
| **Marketplace** | `OfferEvent` | Timeline of offer status changes |
| **Auctions** | `Auction` | Auction records (player, seller, deadline, reserve, status) |
| **Auctions** | `Bid` | Individual bids (buyer, amount, wage, reserved funds, status) |
| **Auctions** | `AuctionEvent` | Timeline of bid and auction events |
| **Deals** | `Deal` | Post-acceptance deal rooms (stage, status, agreed terms) |
| **Deals** | `DealNote` | Club notes within a deal room |
| **Scouting** | `Shortlist` | Club target lists |
| **Scouting** | `ShortlistItem` | Players on a shortlist (priority, notes) |
| **Scouting** | `PlayerInterest` | Interest level and stage per club/player pair |
| **Stats** | `PlayerVendorMap` | Map local players to API-Sports vendor player IDs |
| **Stats** | `PlayerStatsSnapshot` | Raw API stats payloads per player/season/league |
| **Stats** | `PlayerForm` | Computed form scores (0–100) |
| **Stats** | `PlayerStats` | Seasonal stat aggregates |
| **World** | `WorldClub` | Vendor-provided real-world club data |
| **World** | `WorldPlayer` | Vendor-provided real-world player data |
| **World** | `WorldSquadMembership` | Real-world squad membership records |
| **Notifications** | `Notification` | In-app notification records |
| **Auth** | `User`, `Group` | Django users and role groups |

---

## 3. User and club management

### Creating a new user

1. Go to `/admin/auth/user/add/`.
2. Set username and password.
3. Save, then edit the user to assign groups.

### Assigning a role

Add the user to the appropriate group:

| Group | Access |
|---|---|
| `seller` | Create players, auctions, listings; accept bids |
| `buyer` | Place bids; make and respond to offers |
| `admin` | Staff access (all operations) |

### Creating a club for a user

1. Go to `/admin/accounts/clubprofile/add/`.
2. Set **User** (one-to-one), **Name**, and optional fields.
3. Save.

### Verified status

`ClubProfile.verified_status` can be `UNVERIFIED`, `PENDING`, or `VERIFIED`. Change in the admin as part of any club onboarding process.

---

## 4. Finance management

### Viewing a club's budget

Go to `/admin/accounts/clubfinance/` and filter by club.

Fields:

| Field | Meaning |
|---|---|
| `transfer_budget_total` | Total allocated transfer funds |
| `transfer_reserved` | Held for active bids / pending offers |
| `transfer_committed` | Spent on completed deals |
| `wage_budget_total_weekly` | Total weekly wage capacity |
| `wage_reserved_weekly` | Held for pending offer wages |
| `wage_committed_weekly` | Committed to active contracts |

**Remaining = Total − Committed − Reserved** (computed properties; not stored fields).

### Setting budgets

Edit the `ClubFinance` record directly in admin. To reset reserved/committed amounts (e.g. after a season reset), set `transfer_reserved`, `wage_reserved_weekly`, `transfer_committed`, `wage_committed_weekly` all to `0`.

### Initialise finance for a new club

Run:

```bash
python src/manage.py seed_demo
```

Or create the `ClubFinance` record manually in admin.

---

## 5. Player management

### Player status

| Status | Meaning |
|---|---|
| `CONTRACTED` | Has an active `current_club` set |
| `FREE_AGENT` | `current_club` is null; no active club |

Normalise status after bulk edits:

```bash
python src/manage.py normalize_player_status
```

### Making a player a free agent

1. Open the player in `/admin/players/player/<id>/change/`.
2. Clear the **Current club** field.
3. Set **Status** to `FREE_AGENT`.
4. Save.

### Creating a contract

1. Go to `/admin/players/contract/add/`.
2. Set **Player**, **Club**, **Wage weekly**, optional start/end dates.
3. Check **Is active**.
4. Save. The player's `current_club` should also be set to the same club.

### Deactivating a contract

Edit the contract and uncheck **Is active**.

### Player visibility

| Value | Who sees the player |
|---|---|
| `PUBLIC` | All logged-in users |
| `CLUBS_ONLY` | Users with a club profile |
| `PRIVATE` | Only the creating user |

---

## 6. Listings and auctions

### Creating a listing (admin)

1. Go to `/admin/marketplace/listing/add/`.
2. Set **Player**, **Listed by club**, **Listing type** (TRANSFER / LOAN / FREE_AGENT).
3. Set **Visibility** (PUBLIC or INVITE_ONLY).
4. Optionally set **Asking price**, **Min price**, **Deadline**.
5. Set **Status** to `OPEN`.
6. Save.

### Invite-only listings

1. Create the listing with `visibility = INVITE_ONLY`.
2. Go to `/admin/marketplace/listinginvite/add/`.
3. Set the **Listing** and the **Club** to invite.
4. Save. Repeat for each club to invite.

### Closing a listing manually

Edit the listing in admin and set **Status** to `CLOSED` or `WITHDRAWN`.

### Auction mechanics

- Auctions auto-close when read (i.e. any view that calls `close_if_expired(auction)`) if the deadline has passed. There is no background scheduler.
- To force-close an auction, edit the **Deadline** to a past time or directly set **Status** to `CLOSED` in admin.
- To view all bids on an auction, go to `/admin/auctions/bid/?auction__id=<id>`.

---

## 7. Offers and deals

### Offer lifecycle

Offers move through: `DRAFT → SENT → COUNTERED ↔ SENT → ACCEPTED / REJECTED / WITHDRAWN / EXPIRED`.

To manually change an offer's status (e.g. to unstick a broken offer), edit the `Offer` record in admin.

### Creating a deal manually (staff)

A Deal is normally created automatically when a bid or offer is accepted. If you need to create one manually:

1. Go to `/admin/deals/deal/add/`.
2. Link to the relevant `Offer` or `Auction`.
3. Set **Buyer club**, **Seller club**, **Player**, **Agreed fee**, **Agreed wage**.
4. Set **Status** to `IN_PROGRESS` and **Stage** to `AGREEMENT`.
5. Save.

### Completing an auction deal (staff)

Auction deals are set to `PENDING_COMPLETION` when the seller accepts a bid. A staff member must complete them:

**Via the app (staff endpoint):**

```
POST /deals/<id>/staff/complete/
```

This moves the deal to `COMPLETED`, updates the player's `current_club` to the buyer's club, and creates a `Contract` record.

**Via admin:**

Edit the `Deal` record and set **Status** to `COMPLETED`.

### Collapsing a deal (staff)

**Via the app:**

```
POST /deals/<id>/staff/collapse/
```

**Via admin:**

Edit the `Deal` record and set **Status** to `COLLAPSED`.

---

## 8. Scouting oversight

The Scouting section in admin allows you to:

- **Review shortlists:** `/admin/scouting/shortlist/` — see all clubs' target lists.
- **Inspect shortlist items:** filter by shortlist or player to see which clubs are tracking a player.
- **Monitor player interest:** `/admin/scouting/playerinterest/` — see interest levels and stages across all club/player pairs. Useful for identifying who is in active negotiation (`stage=NEGOTIATING`).

No admin actions are typically required; this is primarily a read/oversight view.

---

## 9. Stats and form scores

### Mapping players to vendor IDs

1. Go to `/admin/stats/playervendormap/add/`.
2. Set **Player** (local player record), **Vendor player id** (integer from API-Sports), **Vendor** (default: `api_sports_v3`).
3. Save. Repeat for each player to sync.

### Syncing stats

```bash
python src/manage.py sync_player_stats \
  --season 2025 --league-id 39 \
  --limit 100 --sleep-ms 250
```

Options:
- `--season` — season year (e.g. 2025 for 2024/25 season)
- `--league-id` — API-Sports league ID
- `--limit` — max players to process
- `--sleep-ms` — delay between API calls to respect rate limits

### Computing form scores

```bash
python src/manage.py compute_player_form \
  --season 2025 --league-id 39 --window-games 5
```

Form score (0–100) blends:
- Average match rating over the last `window_games` games (normalised from 0–10 to 0–100)
- Goals + assists per 90 minutes over the same window

The result is stored in `PlayerForm.form_score` and shown on player cards and profiles.

### Generating a stats report

```bash
python src/manage.py stats_report
```

Prints a summary of sync state and form score distribution.

---

## 10. World data

World data (real-world leagues, clubs, and squad memberships) is stored separately from the app's editable `Player` records. It is used as reference/enrichment data.

### Syncing world data

```bash
# Remove duplicates first (safe to skip if DB is clean)
python src/manage.py dedupe_world_data --apply

# Sync a single league (idempotent — uses vendor IDs to avoid duplicates)
python src/manage.py sync_world_league --season 2025 --league-id 39 --sleep-ms 250

# Sync multiple leagues
python src/manage.py sync_world_top5 --season 2025 --leagues "39,140,135,78,61" --sleep-ms 250

# Compute enriched profiles
python src/manage.py compute_world_player_profiles --season 2025 --league-id 39 --limit 500
python src/manage.py compute_world_club_profiles --season 2025 --league-id 39
```

### Common league IDs

| ID | League |
|---|---|
| 39 | Premier League (England) |
| 140 | La Liga (Spain) |
| 135 | Serie A (Italy) |
| 78 | Bundesliga (Germany) |
| 61 | Ligue 1 (France) |

---

## 11. Completing and collapsing deals (staff workflow)

### Auction deals

1. Seller accepts a bid → Deal created with `status=PENDING_COMPLETION`.
2. Staff reviews the deal at `/deals/<id>/`.
3. Staff clicks **Complete deal** (or calls `POST /deals/<id>/staff/complete/`).
4. System: player's `current_club` updated → buyer club; `Contract` record created; `status → COMPLETED`.

### Offer deals

Clubs advance stages themselves:

```
AGREEMENT → PAPERWORK → CONFIRMED → COMPLETED
```

Either club can click **Advance** on the deal page. When CONFIRMED → COMPLETED, the system automatically:
- Creates a `Contract` record for the player with the buyer's club
- Updates `player.current_club` to the buyer club

Staff can intervene by directly editing the `Deal` record in admin if clubs are stuck.

---

## 12. Season management

### Reset season

Deletes all auction/bid/event data, stats snapshots, and form scores. **Preserves** users, clubs, players, contracts, and vendor maps.

```bash
python src/manage.py reset_season --confirm YES
```

After reset, also manually set all `ClubFinance` reserved/committed fields back to `0` in admin, or run `seed_demo` to reinitialise.

### Start a new season

1. Run `reset_season`.
2. Reset finance balances (reserved and committed to 0).
3. Update player contracts (deactivate expired ones, create new ones).
4. Optionally run `normalize_player_status` to clean up player statuses.
5. Optionally re-sync stats for the new season.

---

## 13. Bulk imports

### Import players from CSV

```bash
python src/manage.py import_players_csv \
  --file path/to/players.csv \
  --owner seller1
```

CSV columns:

| Column | Required | Notes |
|---|---|---|
| `name` | Yes | Player full name |
| `age` | Yes | Integer |
| `position` | Yes | GK, DEF, MID, or FWD |
| `valuation` | No | Decimal asking price |

Players are created with `created_by=<owner user>` and default visibility/status.

### Import vendor maps from CSV

```bash
python src/manage.py import_vendor_maps_csv --file path/to/maps.csv
```

CSV columns:

| Column | Required | Notes |
|---|---|---|
| `player_name` | Yes | Must match existing player name exactly |
| `owner_username` | Yes | Username of player's owner |
| `vendor_player_id` | Yes | Integer ID from API-Sports |
| `vendor` | No | Default: `api_sports_v3` |

### Assign demo clubs (utility)

```bash
python src/manage.py assign_demo_clubs
```

Reassigns demo club profiles to their expected users (useful if seed_demo state gets corrupted).

---

## 14. Notifications

Notifications are created programmatically by service functions. There is no admin UI to trigger notifications directly.

### Scheduled notification command

```bash
python src/manage.py notify_upcoming_events
```

Sends notifications for:
- Auctions ending soon (configurable threshold)
- Offers expiring soon

Run this on a cron schedule in production (e.g. every 15 minutes).

### Viewing notifications in admin

Go to `/admin/notifications/notification/` to inspect, filter by recipient or type, and manually mark as read.

---

## 15. Rate limiting

Bid and offer acceptance endpoints are rate-limited using `django-ratelimit`.

Default bid rate: `10/m` per user (configurable via `TRANSFERX_BID_RATE` in `.env`).

**Development:** `LocMemCache` (per-process, resets on restart). Adequate for single-process dev.

**Production:** Must use a shared cache. Configure `CACHES` in settings to use Redis or Memcached:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
    }
}
```

Without a shared cache in production, multiple Gunicorn workers will each have independent rate-limit counters, making limits ineffective.

---

## 16. Anti-sniping configuration

Anti-sniping automatically extends an auction's deadline if a bid is placed within a configured window before it closes.

Set in `.env`:

```bash
TRANSFERX_ENABLE_ANTI_SNIPING=True
TRANSFERX_SNIPING_WINDOW_MINUTES=2    # bid placed within 2 min of deadline triggers extension
TRANSFERX_SNIPING_EXTEND_MINUTES=2    # deadline extended by 2 min
```

Anti-sniping fires in the `place_bid()` service and creates an `AUCTION_EXTENDED` event in the auction timeline.

---

## 17. Production checklist

| Item | Notes |
|---|---|
| `DEBUG=False` | Required; also set `ALLOWED_HOSTS` |
| `SECRET_KEY` | Use a long random string; never commit to source control |
| PostgreSQL | Use a managed Postgres instance; configure `DATABASE_URL` |
| Shared cache | Redis/Memcached required for rate limiting to work across workers |
| Static files | Run `python src/manage.py collectstatic` and serve via CDN or nginx |
| CSS | Run `npm run build:css` before `collectstatic` |
| HTTPS | Set `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` |
| Cron jobs | Schedule `notify_upcoming_events` every 15 minutes |
| Line endings | `docker/web/entrypoint.sh` must use LF (not CRLF) |
| `APISPORTS_KEY` | Required only if using stats sync features |
