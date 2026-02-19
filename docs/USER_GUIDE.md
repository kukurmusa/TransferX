# TransferX User Guide

This guide explains how to use the TransferX web app. Update this file after any major project change.

## Signing in

- Go to `/accounts/login/` and enter your username and password.
- You will be redirected to the dashboard.

## Roles

- Seller: creates players and listings.
- Buyer: places offers on listings.
- Admin: manages the system in Django admin.

## Dashboard

The dashboard shows:
- Active listings
- My listings (sellers)
- My active offers (buyers)
- Hot players (if form scores are available)

## Players (sellers)

- Navigate to `/players/`
- Add a player with the "Add Player" button.
- Edit players you created.

## Listings (formerly Auctions)

### Create a listing (sellers)

- Go to `/auctions/` and click "Create Listing."
- Select a player you own.
- Set deadline and optional reserve price and minimum increment.

### View listings

- `/auctions/` shows all current listings.
- Each listing displays current best offer, minimum next offer, and status.

### Place an offer (buyers)

- Open a listing detail page.
- Enter offer amount and wage offer.
- You can update your offer; it replaces your previous active offer.

### Offer inbox

- Received offers: `/marketplace/offers/received/`
- Sent offers: `/marketplace/offers/sent/`

### Outbid notice

If your offer is lower than the current best, the listing detail page will show an outbid banner.

### Reserve price

- Buyers see reserve met/not met (no numeric value).
- Sellers see the exact reserve price.

## Budgets and wages

- Visit `/accounts/finance/` to see transfer and wage budgets.
- Offers reserve funds; accepted offers commit them.
- When offers are rejected or listings close, reserved funds are released.

## My Club page

- Visit `/accounts/me/` to see budgets, active offers, and your listings.

## Listing timeline

The listing detail page shows a timeline of key events (offers placed/updated, accepted, closed, extended).

## CSV export (sellers)

- On a listing detail page, sellers can export offers as CSV.

## Scouting workflow (M8)

### Targets dashboard

- Visit `/scouting/targets/` for a recruitment overview.
- It shows shortlists, recent updates, expiring offers, and watched players now available.

### Shortlists

- Create and manage shortlists at `/scouting/shortlists/`.
- Add players to a shortlist from the player directory or player profile.

### Interest tracking

- On a player profile, set interest level (Watching/Interested/Priority).
- Update stage (Scouted/Contacted/Negotiating/Dropped).

## Maintenance

Update this file after any major user-facing change.
