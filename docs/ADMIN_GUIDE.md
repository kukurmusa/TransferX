# TransferX Admin Guide

This guide covers operational/admin tasks for running TransferX. Update this file after any major project change.

## Accessing the admin

- URL: `/admin/`
- Use a staff account (e.g., `admin1` from `seed_demo`).

## Key admin sections

- Accounts
  - ClubProfile: club metadata
  - ClubFinance: budgets and reserved/committed balances
- Players
  - Player: local player master
  - Contract: player contracts and wages
- Marketplace
  - Listing: transfer/loan/free-agent listings
  - ListingInvite: invite-only access
  - Offer: negotiation workflow and audit trail
- Scouting
  - Shortlist: club target lists
  - ShortlistItem: players on a shortlist
  - PlayerInterest: interest level/stage tracking
- Auctions
  - Auction, Bid, AuctionEvent: core auction data
- Stats
  - PlayerVendorMap: map local players to vendor IDs
  - PlayerStatsSnapshot: raw vendor payloads
  - PlayerForm: derived form scores
- World
  - WorldClub, WorldPlayer, WorldSquadMembership: vendor-provided data

## Common admin workflows

### Seed demo users

```bash
python src/manage.py seed_demo
```

### Set budgets in bulk

Use the admin action on ClubFinance to reset budgets, or edit per club.

### Reset season (dangerous)

Deletes auctions, bids, events, snapshots, and form scores but keeps users/clubs/players/vendor maps.

```bash
python src/manage.py reset_season --confirm YES
```

### Import players from CSV

```bash
python src/manage.py import_players_csv --file path/to/players.csv --owner seller1
```

CSV columns:
- name, age, position (required)
- valuation (optional)

### Import vendor maps from CSV

```bash
python src/manage.py import_vendor_maps_csv --file path/to/maps.csv
```

CSV columns:
- player_name
- owner_username
- vendor_player_id
- vendor (optional; default api_sports_v3)

### Sync world data

```bash
python src/manage.py sync_world_league --season 2025 --league-id 39 --sleep-ms 250
```

### Scouting oversight

- Review shortlists and interests in the Scouting section.
- Use PlayerInterest to see which clubs are negotiating or tracking targets.

### Deduplicate world data

Run before adding unique constraints if duplicates exist:

```bash
python src/manage.py dedupe_world_data --apply
```

## Rate limiting

- Bid endpoints are rate-limited (default `10/m` per user).
- LocMemCache is used in dev. Use Redis/Memcached in production.

## Maintenance

Update this file after any major operational or admin workflow change.
