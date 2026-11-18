# Local Farm Map — Database Design (V1)

**Version 1.0 · 17 November 2026 · Status: for approval**
Sources: [System Proposal](../../docs/System%20Proposal%20Local%20Farm%20Map.pdf) (2 Nov 2026) · [SRS v1.0](../../docs/Local_Farm_Map_SRS_v1.0.docx) (17 Nov 2026)

---

## 1. Intent

Define the V1 data layer for Local Farm Map: what is stored, how it relates, and the rules that make the pilot's two promises true in the data itself — **freshness** (the map never shows stale listings) and **privacy** (exact farm locations and bulk phone numbers never leave the database).

The single most important query is: *active listings for product X within ~15 km of this point*.

## 2. Goals, non-goals, anti-goals

**Goals**
- Support the pilot at its real scale: one area, 15–20 farms growing to ~50, a handful of listings per farm per day.
- Freshness enforced by data (`expires_at` + query filter), never by a cron job running successfully.
- Privacy enforced by schema: exact coordinates have a private column; public queries touch only `public_location`.
- Keep every spatial detail behind one service layer so the SpatiaLite → PostGIS move is a settings change plus one module swap.
- Preserve listing activity history — the pilot's success metrics (weekly farmer activity) are computed from it.

**Non-goals (V1)**
- Buyer accounts, payments, reservations, reviews, delivery.
- Multiple farms per farmer (BR-05).
- Any V2/V3 feature (WhatsApp updates, alerts, M-Pesa, farmer board).

**Anti-goals**
- A schema whose correctness depends on scheduled jobs.
- Exact coordinates or phone numbers reachable through bulk/map endpoints.
- PostGIS-only features that break the SQLite/SpatiaLite prototype.

## 3. Constraints (from the SRS)

| # | Constraint | Source |
|---|---|---|
| C1 | Django ORM + GeoDjango; custom user model with phone as identifier | SRS 3.1, 7.1 |
| C2 | SQLite + SpatiaLite prototype; PostgreSQL + PostGIS upgrade path | SRS 2.3, 7.1, NFR-12 |
| C3 | One farm per farmer (OneToOne) | BR-05 |
| C4 | Listings expire at midnight local time; only unexpired ones are buyer-visible | BR-06, BR-07, FR-16/17 |
| C5 | Approximate pin by default; exact only on farmer opt-in | BR-08, FR-08/09, NFR-05 |
| C6 | Phone numbers never in bulk/map responses | NFR-06, FR-30 |
| C7 | Prices optional, non-negative KES; phones normalized (E.164); valid coordinates | SRS 5.3 |
| C8 | Expiry enforced by query logic; cleanup job optional | SRS 5.4, A.3 |
| C9 | Fixed V1 catalogue: eggs, milk, honey, vegetables | BR-02, FR-11 |

## 4. Approaches considered

Four decisions shaped the schema. The first was discussed with the project owner; the rest are **my calls**, correctable.

### 4.1 Approximate pins
- *Query-time rounding* — round exact coordinates before returning. No schema change, but every code path that returns a farm must remember to fuzz, forever.
- *Stored public point* — **chosen (owner-approved).** A `public_location` column, grid-snapped when the farmer saves. Exact coordinates never leave the database; privacy is enforced by the model, not discipline. Cost: one column.
- *Named-area table* — pins snap to named sub-locations. Strongest privacy, needs boundary data before day one. Overkill for V1.

Rule: `public_location` = each coordinate of `location` rounded to 2 decimal places (~1.1 km grid; pin sits within ~800 m of the farm, always inside its cell). Regenerated on every farm save, never per-request (per-request jitter would leak the true centroid through averaging).

### 4.2 Manual "town or estate" entry — *my call*
- *External geocoder* (e.g. Nominatim) — network dependency, rate limits, usage policy.
- *Curated `Place` table* — **chosen.** A handful of pilot-area towns/estates with coordinates and a search radius, seeded by the admin. No external dependency; doubles as the pilot-area registry. Answers SRS open question "how to convert manual entry to coordinates".

### 4.3 Farmer authentication — *my call*
- *OTP/SMS* — needs an SMS gateway and per-message cost during the pilot.
- *Phone-as-username + password (Django auth)* — **chosen.** Zero external dependency, standard `AbstractUser` shape. OTP can be layered on in V2 alongside WhatsApp/SMS updates. Answers SRS open question on the verification mechanism.

### 4.4 Listing renewal & history — *my call*
- *One row per farm–product, updated in place* — simplest, but destroys the activity history the pilot metrics need.
- *One row per farm–product–day* — **chosen.** `UNIQUE (farm, product, listing_date)`; renewal is an upsert. Weekly-activity metrics are a simple query. Answers SRS open question on retention with "keep everything through the pilot".

## 5. Data model

### 5.1 `User` — custom Django user (`AUTH_USER_MODEL`)

| Field | Type | Rules |
|---|---|---|
| id | PK | |
| phone_number | varchar(20), UNIQUE, NOT NULL | E.164 (`+254…`), the `USERNAME_FIELD` |
| name | varchar(120) | |
| role | enum `farmer` / `admin`, default `farmer` | buyers never get rows (BR-03) |
| password | hash | Django PBKDF2 |
| is_active, is_staff | bool | `is_staff` gates Django admin (FR-36) |
| created_at / updated_at | timestamptz (UTC) | |

### 5.2 `Farm`

| Field | Type | Rules |
|---|---|---|
| id | PK | |
| owner | OneToOne → User, `PROTECT` | enforces BR-05; deactivate users, don't delete |
| name | varchar(140) | |
| location | Point, SRID 4326, NOT NULL | **exact — private.** Never selected in public querysets |
| public_location | Point, SRID 4326, NOT NULL | grid-snapped copy (see 4.1); the only geometry public queries return |
| show_exact_pin | bool, default false | FR-08/09; when true, detail view may serve `location` |
| is_active | bool, default false | **my call** — public-visibility gate: farm stays out of discovery until an admin activates it at onboarding (proposal: farms are personally onboarded) |
| pickup_hours | text | free text, e.g. "Mon–Sat, 7am–6pm" |
| contact_phone | varchar(20) | E.164; served only on the farm detail endpoint |
| whatsapp_number | varchar(20), NULL | E.164; forms default it to `contact_phone` |
| products | M2M → Product | the farm's offered catalogue (FR-07) |
| created_at / updated_at | timestamptz (UTC) | |

### 5.3 `Product` — fixed V1 catalogue

| Field | Type | Rules |
|---|---|---|
| id | PK | |
| name | varchar(60) | eggs, milk, honey, vegetables |
| slug | varchar(60), UNIQUE | filter key in URLs/querysets |
| category | varchar(60) | equals `name` in V1; kept per SRS Table 14 for future catalogue growth |
| unit | varchar(20) | tray / litre / kg / bunch … |
| is_active | bool, default true | admin deactivates; never delete (listings reference it) |

Seeded by a Django data migration.

### 5.4 `Listing`

| Field | Type | Rules |
|---|---|---|
| id | PK | |
| farm | FK → Farm, CASCADE | |
| product | FK → Product, PROTECT | |
| listing_date | date (pilot-local) | local calendar day of creation/renewal |
| quantity_note | varchar(140), NULL | FR-14 |
| price_kes | decimal(8,2), NULL, CHECK ≥ 0 | optional (FR-13) |
| withdrawn_at | timestamptz, NULL | **my call** — early "sold out" removal; answers SRS open question |
| created_at | timestamptz (UTC) | FR-15 |
| expires_at | timestamptz (UTC), NOT NULL | midnight end of `listing_date` in pilot-local time (FR-16) |

Constraints and indices:
- `UNIQUE (farm, product, listing_date)` — renewal is an upsert on this key.
- `CHECK (expires_at > created_at)`, `CHECK (price_kes IS NULL OR price_kes >= 0)`.
- Index `(product_id, expires_at)` — serves the discovery query; index `(farm_id, listing_date)` — serves the farmer dashboard.
- **Active listing** = `expires_at > now() AND withdrawn_at IS NULL`, enforced in a single default queryset/manager, per SRS 5.4 (correctness never depends on the cleanup job).

### 5.5 `Place` — manual location search — *my call*

| Field | Type | Rules |
|---|---|---|
| id | PK | |
| name | varchar(120) | e.g. town or estate |
| slug | varchar(120), UNIQUE | |
| location | Point, SRID 4326 | search origin |
| search_radius_m | int, default 15000 | per-place override of the 15 km example radius |
| is_active | bool, default true | |
| display_order | int | ordering in the picker |

### 5.6 `ContactEvent` — counting buyer contact taps — *my call*

The proposal's pilot success metrics include *"number of buyer contacts (calls or WhatsApp taps) per week"* — unmeasurable if the Call/WhatsApp buttons are pure `tel:`/`wa.me` links, because no server ever sees the tap. So the farm detail view routes contact buttons through a lightweight redirect endpoint (`GET /contact/{farm}/{channel}` → logs the event → 302 to the `tel:`/`wa.me` URL), which makes the metric a simple query.

| Field | Type | Rules |
|---|---|---|
| id | PK | |
| farm | FK → Farm, PROTECT | |
| channel | enum `call` / `whatsapp` | |
| listing | FK → Listing, NULL | the listing shown when tapped, when known |
| created_at | timestamptz (UTC) | |

Deliberately stores **nothing about the buyer** — no phone, IP, or user agent. Counts only.

## 6. Relationships

```mermaid
erDiagram
    USER ||--o| FARM : "owns (1:1)"
    FARM ||--o{ LISTING : "has"
    PRODUCT ||--o{ LISTING : "appears in"
    FARM }o--o{ PRODUCT : "offers (M:N)"
    FARM ||--o{ CONTACT_EVENT : "receives"

    USER {
        bigint id PK
        string phone_number UK "E.164 - username"
        string name
        enum role "farmer|admin"
        string password "hash"
        bool is_staff
        timestamptz created_at
    }
    FARM {
        bigint id PK
        bigint owner_id FK_UK
        string name
        geometry location "exact - private"
        geometry public_location "grid-snapped ~1km"
        bool show_exact_pin "default false"
        bool is_active "default false - admin gate"
        text pickup_hours
        string contact_phone "detail view only"
        string whatsapp_number "nullable"
        timestamptz created_at
    }
    PRODUCT {
        bigint id PK
        string name
        string slug UK
        string category "equals name in V1"
        string unit
        bool is_active
    }
    LISTING {
        bigint id PK
        bigint farm_id FK
        bigint product_id FK
        date listing_date "pilot-local"
        string quantity_note "nullable"
        decimal price_kes "nullable >=0"
        timestamptz withdrawn_at "nullable"
        timestamptz created_at
        timestamptz expires_at "indexed"
    }
    PLACE {
        bigint id PK
        string name
        string slug UK
        geometry location
        int search_radius_m "default 15000"
        bool is_active
        int display_order
    }
    CONTACT_EVENT {
        bigint id PK
        bigint farm_id FK
        enum channel "call|whatsapp"
        bigint listing_id FK "nullable"
        timestamptz created_at
    }
```

`Place` is standalone — a search-origin registry, unrelated to farms.

## 7. Key queries

**Q1 — Buyer discovery (the main query).** Active listings for product X within the search radius of point P:

```sql
SELECT l.id, f.id, f.name, f.pickup_hours,
       CASE WHEN f.show_exact_pin THEN f.location
            ELSE f.public_location END AS pin
FROM listing l
JOIN farm f ON f.id = l.farm_id
WHERE l.product_id = :product
  AND l.expires_at > now()
  AND l.withdrawn_at IS NULL
  AND ST_DWithin(f.location, :point, :radius_m);
```

Notes: distance filters on the **exact** `location` (correct membership), while the returned pin honours the opt-in. No phone fields in the SELECT. Discovery also excludes farms whose owner account has been deactivated and farms not yet activated (`is_active = false`, curated onboarding). Encoded in the ORM behind a `discovery` service module.

**Q2 — Farm detail.** Farm row + its active listings (contact fields allowed here and only here).

**Q3 — Farmer dashboard.** Today's rows for the farm in any state (so the UI can pre-check "available today").

**Q4 — Pilot metrics.** Per-farm count of distinct `listing_date` values per week — directly enabled by the one-row-per-day design (§4.4).

**Q5 — Contact metrics.** Weekly count of `ContactEvent` rows, overall and per farm/channel — the proposal's "buyer contacts per week" success measure, served by the index below.

## 8. Indexes

| Table | Index | Serves |
|---|---|---|
| listing | `(product_id, expires_at)` | Q1 |
| listing | `(farm_id, listing_date)` | Q3 |
| listing | unique `(farm, product, listing_date)` | renewal upsert |
| farm | spatial index on `location` | Q1 |
| user | unique `phone_number` | login |
| contact_event | `(created_at)` | Q5 weekly counts |
| place | unique `slug` | picker |

On PostGIS add a `GistIndex` on `farm.location` in model `Meta.indexes`; SpatiaLite creates its R-tree automatically.

## 9. Time and expiry

- `USE_TZ = True`; all timestamps stored UTC.
- Pilot timezone assumed **Africa/Nairobi** — *my call*, confirm with the pilot-area decision (SRS open question). It is a settings value, not a schema change.
- `listing_date` = local calendar date at creation/renewal; `expires_at` = that day's midnight converted to UTC.
- The optional cleanup job only tidies old rows; visibility always comes from the query filter (C8).

## 10. Spatial portability (SpatiaLite → PostGIS)

- Store everything in SRID 4326; never store projected coordinates.
- PostGIS: distance in metres via geography cast (`Distance(..., geography=True)` / `ST_DWithin` on geography).
- SpatiaLite: no geography type — inside the discovery service, transform both the farm point and the origin to the pilot's local UTM zone and compare metres there. Kenya straddles 36°E: pilot area west of it → SRID 32736, east (e.g. Nairobi) → 32737. **Decided by the pilot-area choice, not by the builder.**
- All spatial SQL lives in the `discovery` service layer (SRS A.3), so the migration is: swap that module's distance helper + change `DATABASES` settings.

## 11. Retention — *my call*

Keep expired and withdrawn listing rows for the whole pilot (Q4 needs them). Deletion/archival policy is a post-pilot review decision (SRS 5.4).

## 12. My calls (veto any of these)

1. **Password auth**, phone-as-username — no SMS dependency in V1; OTP layer in V2 (§4.3).
2. **`Place` table** for manual location entry instead of an external geocoder (§4.2).
3. **`withdrawn_at`** on Listing for early "sold out" removal (§5.4).
4. **One listing row per farm–product–day** for activity history (§4.4).
5. **`pickup_hours` as free text** — structured hours are overkill for V1.
6. **`category` kept on Product** though it equals `name` in V1 — per SRS Table 14, future-proofing.
7. **Africa/Nairobi** as the expiry timezone — pending pilot-area confirmation (§9).
8. **PROTECT** on farm→owner and listing→product FKs — deactivate, never delete, pilot history.
9. **`ContactEvent` + redirect endpoint** to count buyer contact taps (§5.6) — required by the proposal's success metrics; stores nothing about the buyer.
10. **`Farm.is_active` visibility gate**, default off — the pilot onboards farms in person (proposal rollout); a farm appears in discovery only after admin activation (§5.2).

**Open dependency (yours, not mine):** the pilot area itself. It decides the real `Place` seed rows, the UTM zone constant (§10) and confirms the §9 timezone. Table shapes don't depend on it, so it blocks seeding/deployment — not this design.

## 13. Left to the builder

- Django model code, migrations, and the seed data migration (Product, initial Places).
- The grid-snap helper (round to 2 dp) in the farms service, invoked on save.
- The `discovery` service module incl. the SRID strategy from §10.
- A `Listing` manager exposing the "active" queryset used everywhere buyer-facing.
- Django admin registration for all six models (FR-35/36).
- The contact redirect endpoint (`GET /contact/{farm}/{channel}` → 302 `tel:`/`wa.me`) that feeds `ContactEvent`.
- Phone normalization approach (e.g. `django-phonenumber-field`) — builder's choice, E.164 in the schema either way.
