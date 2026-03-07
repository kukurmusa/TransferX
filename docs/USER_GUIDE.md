# TransferX User Guide

TransferX is a football player transfer marketplace. Clubs buy, sell, and loan players through auctions and direct offers. This guide explains every feature and the typical workflows for each role.

---

## Table of Contents

1. [Roles and accounts](#1-roles-and-accounts)
2. [Signing in](#2-signing-in)
3. [Navigation and layout](#3-navigation-and-layout)
4. [Dashboard (War Room)](#4-dashboard-war-room)
5. [Player marketplace (Browse)](#5-player-marketplace-browse)
6. [Player profiles](#6-player-profiles)
7. [Listings hub](#7-listings-hub)
8. [Auctions](#8-auctions)
9. [Direct offers](#9-direct-offers)
10. [Deal rooms](#10-deal-rooms)
11. [Scouting](#11-scouting)
12. [Club directory](#12-club-directory)
13. [Finance](#13-finance)
14. [My Club page](#14-my-club-page)
15. [Notifications](#15-notifications)
16. [Free agents](#16-free-agents)
17. [Typical end-to-end workflows](#17-typical-end-to-end-workflows)

---

## 1. Roles and accounts

Every user belongs to one of three roles that control what actions are available.

| Role | Can do |
|---|---|
| **Seller** | Create and manage players; create auctions and listings; accept bids and offers; advance deal stages |
| **Buyer** | Search players; place bids on auctions; make direct offers; advance deal stages |
| **Admin** | Everything above, plus Django admin access; can complete or collapse any deal |

A user can only have one active club. All financial tracking (budgets, reservations, commitments) is per club.

---

## 2. Signing in

1. Go to `/accounts/login/`.
2. Enter your username and password.
3. After login you are redirected to the **Dashboard** (`/dashboard/`).

To sign out, click **Sign out** in the bottom of the sidebar.

---

## 3. Navigation and layout

The sidebar on the left is the main navigation. It collapses to icon-only on small screens and can be toggled with the hamburger button on mobile.

### Sidebar sections

| Section | Links |
|---|---|
| **MARKET** | Browse Players, Listings, Free Agents |
| **MY DEALS** | Auctions, Inbox (received offers), Sent Offers |
| **CLUB** | Dashboard, My Club, Finance |
| **SCOUTING** | Targets, Shortlists |
| **ADMIN** | Admin Panel *(staff only)* |

The sidebar remembers its collapsed/expanded state between visits.

A **notification bell** in the sidebar header shows unread notification count. Click it to open the notification list.

A **deal badge** in the sidebar shows how many deals are currently In Progress.

---

## 4. Dashboard (War Room)

**URL:** `/dashboard/`

The War Room is the main operational hub. It surfaces the most important activity across all areas.

### Stats bar

Four summary cards at the top:

| Card | What it shows |
|---|---|
| Squad size | Total players in your club's squad |
| Active listings | Auctions and listings currently open |
| Open offers | Offers in SENT or COUNTERED state |
| Shortlisted players | Players tracked across all your shortlists |

### Active auctions panel

Lists every auction you are involved in (as seller or active bidder). Refreshes automatically every 15 seconds via HTMX polling. For each auction:

- Player name, club, position
- Time remaining (live countdown updated every second)
- Your current bid amount (if bidding)
- Current best bid
- Whether you are the current top bidder

Click any row to go to the full auction detail page.

### Offers requiring action

Offers where it is your turn to respond — i.e., the other party last acted (sent, countered) and is waiting for you. Shows:

- Player name
- Counterparty club
- Transfer fee and weekly wage
- Offer status badge

Click an offer to open the offer negotiation page.

### Scouting alerts

Automatically generated alerts about players you are tracking:

- **New listings** — a shortlisted player has a new public listing
- **Price changes** — a listed player's asking price changed
- **Offers expiring soon** — active offers on shortlisted players expire within 72 hours
- **Now available** — a shortlisted player has become a free agent or been listed

### Recent notifications

The five most recent notifications. Click **View all** to open the full notification centre.

---

## 5. Player marketplace (Browse)

**URL:** `/players/market/`

The main searchable directory of all players available on the platform. Defaults to showing contracted and free-agent players who are publicly visible or open to offers.

### Filters (left panel)

| Filter | Options |
|---|---|
| Search | Free-text search on player name |
| Position | All / GK / DEF / MID / FWD |
| Age | Slider range (e.g. 18–28) |
| Form | Minimum form score (0–100) |
| Availability | Checkboxes: Listed for transfer, Listed for loan, Free agent, Open to offers |
| Nationality | Free-text |
| Sort | Newest, Form (high→low), Age (asc/desc) |

Filters apply instantly via HTMX (no page reload). The URL updates so filtered results can be bookmarked or shared.

### Player cards

Each card shows:

- Player photo (or initials avatar)
- Position badge (colour-coded: GK=amber, DEF=blue, MID=emerald, FWD=red)
- Form score (top right)
- Player name, current club with crest, nationality flag
- Stats grid: Rating / Goals+Assists / Minutes
- Form bar (gradient from emerald to red, scaled to 0–100)
- Availability status badge (Free Agent / Loan / Transfer / Open to offers / Contracted)
- **View profile →** link

Results are paginated 24 per page with Prev / Next controls at the bottom.

---

## 6. Player profiles

**URL:** `/players/market/<id>/`

Full profile page for any player in the marketplace.

### Sections

**Bio header**
- Large photo or avatar
- Position badge, nationality flag, age
- Current club name with crest (or "Free agent")
- Status badges (contracted / free agent / open to offers)

**Performance snapshot**
- Minutes played, Goals, Assists, Avg Rating (from latest stats snapshot)
- Form score bar (0–100)
- Form trend indicator (up/down/neutral)

**Current listing** *(shown if a public listing or invited listing exists)*
- Listing type (Transfer / Loan / Free Agent)
- Asking price and deadline
- Link to the listing hub page

**Scouting controls** *(club users only)*
- **Add to shortlist** — pick which shortlist to add the player to, set priority (1–5) and optional notes
- **Set interest** — mark interest level (Watching / Interested / Priority) and stage (Scouted / Contacted / Negotiating / Dropped)
- If already on a shortlist or interest set, shows current values with edit/remove options

**Make offer button**
- Visible to buyers with a club; goes to `/marketplace/offers/new/?player=<id>`

---

## 7. Listings hub

**URL:** `/listings/`

A separate browse page focused on formal listings created by sellers. Each listing represents a player the seller has explicitly put up for:

- **Transfer** — permanent sale
- **Loan** — temporary transfer
- **Free agent** — no current club, available immediately

### Listing card

- Player name, position, nationality
- Listing type badge
- Asking price (if set)
- Deadline (if set)
- Listed by club
- **View listing** link

### Listing detail

**URL:** `/listings/<id>/`

- Full player bio
- Listing terms: type, asking price, deadline, notes
- **Make offer** button (links to offer form pre-filled with this listing)
- Invite-only listings are only visible to clubs that have been invited by the seller

---

## 8. Auctions

Auctions are the public, competitive bidding mechanism. Multiple buyers compete by placing increasing bids before a deadline.

### Browsing auctions

**URL:** `/auctions/`

Lists all open auctions. For each auction:

- Player name, position, club
- Current best bid amount
- Number of active bids
- Time remaining (deadline)
- Player form score
- Minimum next bid amount

Auctions automatically close when read if their deadline has passed.

Sort options: **Deadline soonest** or **Form (high→low)**.

---

### Creating an auction *(sellers only)*

**URL:** `/auctions/new/`

1. Select a player from your squad.
2. Set the deadline (date and time).
3. Optionally set a **reserve price** — the minimum bid you will accept. Buyers only see whether the reserve has been met or not, not the exact value.
4. Optionally set a **minimum increment** — the minimum amount each subsequent bid must increase above the current best.
5. Submit to publish the auction as OPEN.

---

### Auction detail page

**URL:** `/auctions/<id>/`

The main page for an active auction. Layout differs slightly for sellers and buyers.

**Player card** — photo, name, position, club, contract status.

**Deadline countdown** — live countdown timer. Updates every second. If anti-sniping is enabled and a bid is placed within the configured window of the deadline, the deadline is automatically extended.

**Current best bid** — the highest active bid amount.

**Minimum next bid** — best bid + minimum increment (or £1 if no increment set, or the starting price if no bids yet).

**Reserve status** — "Reserve met" or "Reserve not yet met" (shown to buyers). Sellers see the exact reserve price.

**Player form card** — form score, average rating, goals and assists.

**Bid ladder (buyers view)**
- Shows all active bids ordered highest to lowest
- Refreshes automatically every few seconds via HTMX
- Your own bid is highlighted
- An "Outbid" banner shows if you are no longer the top bidder

**Bid form (buyers only)**
- Enter your bid amount (must be ≥ minimum next bid)
- Enter weekly wage offer (optional)
- Add optional notes
- Submitting replaces your previous active bid (funds are re-reserved accordingly)
- Rate-limited: maximum 10 bids per minute per user by default

**Seller bids table (seller view)**
- Shows all bids with buyer club names, amounts, wages, notes, timestamps
- Seller can **accept** any active bid to end the auction

**Timeline**
- Log of all auction events: bids placed, bids replaced, auction extended, auction accepted/closed

**CSV export (sellers only)**
- Download all bids as a CSV file: bid ID, timestamp, buyer club, amount, wage offer, status, notes

---

### Accepting a bid *(sellers only)*

1. On the auction detail page, scroll to the seller bids table.
2. Click **Accept** next to the bid you want to accept.
3. The auction status changes to ACCEPTED.
4. A Deal room is created automatically (see [Deal rooms](#10-deal-rooms)).
5. All other bids are withdrawn; reserved funds are released.

---

### Anti-sniping

If enabled by the operator, any bid placed within the configured window before the deadline (default: 2 minutes) automatically extends the deadline by the configured amount (default: 2 minutes). This prevents last-second sniping.

---

## 9. Direct offers

Direct offers allow clubs to negotiate privately without a public auction. An offer goes through a structured lifecycle.

### Offer statuses

| Status | Meaning |
|---|---|
| **DRAFT** | Created but not yet sent |
| **SENT** | Sent to the other club; awaiting response |
| **COUNTERED** | The receiving club has countered with different terms |
| **ACCEPTED** | Both sides have agreed; a Deal is created |
| **REJECTED** | The receiving club has declined |
| **WITHDRAWN** | The sending club has pulled the offer |
| **EXPIRED** | The offer deadline passed without resolution |

---

### Making an offer *(buyers)*

**URL:** `/marketplace/offers/new/?player=<id>`

1. Navigate to a player profile and click **Make offer**, or go to the URL directly.
2. Fill in:
   - **Transfer fee** — the total fee amount
   - **Weekly wage** — proposed weekly wage for the player
   - **Contract years / Contract end date** — proposed contract length
   - **Notes / message** — optional opening message
   - **Expiry date** — optional deadline for the offer to remain open
3. Send the offer. It appears in your **Sent Offers** list and in the receiving club's **Inbox**.

> Free agent offers can be sent but acceptance is blocked until the player is onboarded by an admin.

---

### Offers inbox (received offers)

**URL:** `/marketplace/offers/received/` (also linked as "Inbox" in the sidebar)

Displays all offers received by your club, split into two groups:

- **Needs your response** — the other club sent or countered; it is your turn to act
- **Awaiting their reply** — you sent or countered; waiting for the other club

Each offer card shows: player name, from/to club, fee, weekly wage, last activity, expiry, and the last message snippet.

---

### Sent offers

**URL:** `/marketplace/offers/sent/`

Same layout as the inbox but showing offers your club has sent.

---

### Offer detail and negotiation

**URL:** `/marketplace/offers/<id>/`

The full negotiation thread for a single offer.

**Offer terms** — current fee, wage, contract years, contract end date.

**Offer timeline** — chronological log of all events: created, sent, countered, messages.

**Message thread** — club messages attached to the offer.

**Action buttons** (which appear depends on the offer status and your role):

| Button | Who can use it | What it does |
|---|---|---|
| **Counter** | Receiving club (when SENT) or either club (when COUNTERED) | Opens a counter-offer form with pre-filled current terms to adjust |
| **Accept** | Receiving club (when SENT or COUNTERED) | Accepts the offer; creates a Deal room |
| **Reject** | Receiving club (when SENT or COUNTERED) | Rejects; offer status → REJECTED |
| **Withdraw** | Sending club (when SENT or COUNTERED) | Withdraws; offer status → WITHDRAWN |
| **Send message** | Either club (when SENT or COUNTERED) | Adds a message without changing terms |

---

### Countering an offer

1. On the offer detail page click **Counter**.
2. The counter form is pre-filled with the current terms.
3. Adjust fee, wage, contract length, or add a message.
4. Submit — the offer status becomes COUNTERED and the other club is notified.

---

## 10. Deal rooms

A Deal room is created when either:
- A seller accepts an auction bid
- A club accepts a direct offer

**URL:** `/deals/` (list) · `/deals/<id>/` (room)

---

### Deal list

Shows all deals your club is a party to (as buyer or seller). Grouped by status:

| Status | Meaning |
|---|---|
| **IN_PROGRESS** | Active negotiation/paperwork underway |
| **PENDING_COMPLETION** | Auction deal awaiting staff confirmation |
| **COMPLETED** | Transfer finalised |
| **COLLAPSED** | Deal fell through |

---

### Deal room (detail)

**Header** — Player name, buyer club → seller club, status badge.

**Agreed terms** — Transfer fee and weekly wage agreed at acceptance.

**Stage progress** *(offer-based deals only)*

Offer deals move through four stages in order:

```
AGREEMENT → PAPERWORK → CONFIRMED → COMPLETED
```

- **AGREEMENT** — clubs have agreed terms; initial stage
- **PAPERWORK** — contracts and documentation in progress
- **CONFIRMED** — all documents signed; transfer confirmed
- **COMPLETED** — player officially transferred; contract and club updated automatically

Either party can click **Advance to next stage** to move forward. At COMPLETED, the player's `current_club` is updated and a contract record is created.

**Auction deals** skip the stage UI and show PENDING_COMPLETION until a staff member marks the deal complete via the admin panel or staff endpoint.

**Collapse deal** — Either party can collapse a deal if it falls through. Status → COLLAPSED.

**Notes section** — A shared conversation thread between the two clubs. Both clubs can add notes visible to each other. Shows who posted each note and when.

---

## 11. Scouting

The scouting module helps clubs track potential transfer targets before making any formal approach.

### Targets dashboard

**URL:** `/scouting/targets/`

A high-level overview of your scouting activity:

- **Shortlists summary** — your shortlists with item counts and last-updated timestamps
- **Recent updates** — shortlist items whose status or notes changed recently
- **Expiring offers** — active offers on scouted players expiring within 72 hours
- **Watched players now available** — players on your shortlists who have recently become free agents or received a new public listing

---

### Shortlists

**URL:** `/scouting/shortlists/`

Manage your club's target lists.

**Creating a shortlist:**
1. Click **New shortlist**.
2. Enter a name (required) and optional description.
3. Submit — the new shortlist appears in your list.

Each club can have multiple shortlists (e.g., "Summer window 2026 targets", "Goalkeeper search").

---

### Shortlist detail (Kanban board)

**URL:** `/scouting/shortlists/<id>/`

Players on the shortlist are organised into four priority columns:

| Column | Priority value |
|---|---|
| **High** | P1 |
| **Medium** | P2 |
| **Low** | P3 |
| **Monitor** | P4+ |

**Each player card shows:**
- Player name and photo
- Current club and position
- Form score
- Open listing indicator (if a listing exists for this player)
- Priority badge and any notes

**Adding a player:**
- From the shortlist page: click **Add player**, enter the player name or ID, set priority and notes.
- From any player profile: click **Add to shortlist**, select the shortlist, priority, and notes.

**Updating a player:**
- Click the edit icon on any card to update priority or notes inline.

**Removing a player:**
- Click the remove icon on any card.

**Drag and drop:**
- Cards can be dragged between columns to change priority.

**Search:**
- A search box filters the kanban view to matching player names without reloading.

**Shortlist settings:**
- A collapsible panel at the top allows renaming or deleting the shortlist.

---

### Player interest tracking

Interest is per-club, per-player metadata that tracks how seriously you are pursuing a player.

**Set interest from a player profile:**
1. Go to the player's profile page (`/players/market/<id>/`).
2. Click **Set interest**.
3. Choose an **Interest level:**
   - **Watching** — monitoring the player, no active pursuit
   - **Interested** — considering making an approach
   - **Priority** — actively pursuing; high recruitment priority
4. Choose a **Stage:**
   - **Scouted** — identified and assessed
   - **Contacted** — initial contact made
   - **Negotiating** — active negotiations underway
   - **Dropped** — no longer pursuing
5. Add optional notes.

Interest can be cleared at any time from the player profile.

---

## 12. Club directory

**URL:** `/clubs/`

Browse all clubs registered on the platform.

Each club card shows: club name, crest, city, league, verification status.

**Club detail page:** `/clubs/<id>/`

- Club crest, name, city, league
- Verified status badge
- Current squad overview (if public)
- Contact information (if available)

---

## 13. Finance

**URL:** `/accounts/finance/`

Full breakdown of your club's financial position.

### Transfer budget

| Row | Meaning |
|---|---|
| **Total** | The total transfer budget allocated to your club |
| **Committed** | Funds locked in completed deals |
| **Reserved** | Funds temporarily held for pending bids and offers |
| **Remaining** | Available = Total − Committed − Reserved |

A progress bar visualises committed (emerald), reserved (amber), and available (slate) portions.

### Weekly wage budget

Same breakdown for the weekly wage budget:

| Row | Meaning |
|---|---|
| **Total** | Total weekly wage budget |
| **Committed** | Weekly wages locked in completed contracts |
| **Reserved** | Wages temporarily held for pending offers |
| **Remaining** | Available weekly wage capacity |

### How funds move

1. **Bid placed or offer sent** → amount moves from Available to **Reserved**.
2. **Bid/offer withdrawn, rejected, or outbid** → Reserved funds return to Available.
3. **Bid/offer accepted** → Reserved moves to **Committed** when the deal completes.

---

## 14. My Club page

**URL:** `/accounts/me/`

A snapshot of your club's current activity:

- **Budget cards** — transfer remaining and weekly wage remaining
- **My listings** — auctions you have created, with current bid count and status
- **My active bids** — auctions you are bidding on; shows your bid amount, current best bid, and whether you are outbid

---

## 15. Notifications

**URL:** `/notifications/`

In-app notification centre. The sidebar bell icon shows the unread count (updated in the background).

### Notification types

| Type | When it fires |
|---|---|
| **OUTBID** | Another buyer has placed a higher bid on an auction you bid on |
| **AUCTION_BID_RECEIVED** | Someone placed a bid on your auction |
| **AUCTION_ENDING** | An auction you are involved in is ending soon |
| **AUCTION_BID_ACCEPTED** | Your bid was accepted by the seller |
| **OFFER_RECEIVED** | A club has sent you a direct offer |
| **OFFER_ACCEPTED** | Your offer was accepted |
| **OFFER_REJECTED** | Your offer was rejected |
| **OFFER_COUNTERED** | The other club countered your offer |
| **OFFER_EXPIRING** | One of your open offers is expiring soon |
| **LISTING_NEW_OFFER** | Your listing received a new offer |
| **DEAL_COMPLETED** | A deal you are party to has completed |
| **DEAL_COLLAPSED** | A deal you are party to has collapsed |
| **PLAYER_AVAILABLE** | A player you shortlisted has become available |

### Actions

- Click any notification to navigate to the related page (marked as read automatically).
- Click **Mark all read** to clear the badge count.

---

## 16. Free agents

**URL:** `/players/free-agents/`

A filtered view of the player marketplace showing only players with no current club (status = FREE_AGENT) or players listed as free agents.

Same filters as the main player marketplace (position, age, form, search, sort). Click any player card to go to their full profile.

---

## 17. Typical end-to-end workflows

### Workflow A — Auction (seller sells a player via public bidding)

```
Seller creates player
  └─> Seller creates auction (set player, deadline, optional reserve/increment)
        └─> Buyers browse /auctions/
              └─> Buyer places bid (amount + wage offer)
                    └─> Other buyers outbid → notifications sent
                          └─> Seller reviews bids, accepts the best one
                                └─> Deal created (PENDING_COMPLETION)
                                      └─> Staff marks deal complete → COMPLETED
                                            └─> Player's current_club updated
```

### Workflow B — Direct offer (buyer approaches a listed player)

```
Seller creates listing (TRANSFER/LOAN/FREE_AGENT)
  └─> Buyer browses /listings/ or /players/market/
        └─> Buyer makes offer (fee, wage, contract terms)
              └─> Seller receives offer in Inbox
                    └─> Seller counters (adjusts terms) OR accepts OR rejects
                          └─> If countered: buyer receives counter in Sent Offers
                                └─> Buyer counters back OR accepts OR withdraws
                                      └─> On acceptance: Deal created (IN_PROGRESS, stage=AGREEMENT)
                                            └─> Clubs advance stages: AGREEMENT → PAPERWORK → CONFIRMED → COMPLETED
                                                  └─> Player transferred: current_club updated, contract created
```

### Workflow C — Scouting pipeline (finding and tracking targets)

```
Buyer creates a shortlist ("Summer 2026 Targets")
  └─> Buyer browses /players/market/ with filters
        └─> Buyer adds promising players to shortlist (set priority P1/P2/P3)
              └─> Buyer sets interest level (Watching → Interested → Priority)
                    └─> Targets dashboard shows alerts when shortlisted players get new listings
                          └─> Buyer initiates offer from player profile
                                └─> Offer workflow (Workflow B)
```

### Workflow D — Checking your financial position

```
Club has budget set by admin
  └─> Club places bids/makes offers → funds reserved
        └─> /accounts/finance/ shows remaining = total − committed − reserved
              └─> On deal completion → reserved → committed
                    └─> On bid outbid or offer rejected → reserved released back to available
```
