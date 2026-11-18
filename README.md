# Local Farm Map

A mobile-first web app that shows nearby households which farms are selling
fresh food **today** — eggs, milk, honey and vegetables — and lets small
farmers publish availability in a few taps. Buyers call or WhatsApp the
farmer and pay at the farm gate; the platform never holds money.

Part of a one-area pilot centred on **Kisii University, Kenya**.

## How it works

- **Buyers** browse without an account: pick an area (or use GPS), filter by
  product, and get a map of nearby farms with prices. Listings expire at
  midnight, so the map never shows stale stock.
- **Farmers** register with a phone number, create a farm profile, and renew
  availability daily in under 10 seconds.
- **Privacy by default:** buyers see an approximate pin (~1 km grid); the
  exact location is opt-in, and phone numbers appear only on a farm's detail
  page.
- Pilot metrics (weekly farmer activity, buyer contact taps) are logged in
  the database and printable via `manage.py pilot_report`.

## Layout

| Path | What it is |
|---|---|
| `docs/` | Project proposal (PDF) and SRS v1.0 |
| `design/database/` | Database design (6 tables, constraints, queries) |
| `design/system/` | System Design Document (lean architecture) |
| `design/uiux/` | UI/UX design — screens, journeys, wireframes |
| `design/UML/` | Use-case, class, sequence, activity, component diagrams |
| `farmconnect/` | The Django application |

## Stack

Django 4.2 · GeoDjango · Jinja2 templates · Tailwind CSS (compiled, no CDN)
· Leaflet + OpenStreetMap · SQLite/SpatiaLite (prototype) with a
PostgreSQL/PostGIS upgrade path · installable PWA.

## Running locally

```bash
# SpatiaLite support (Debian/Ubuntu)
sudo apt-get install -y libsqlite3-mod-spatialite

cd farmconnect
python3 manage.py migrate          # creates + seeds the 4-product catalogue
python3 manage.py seed_demo_data   # demo farms & places around Kisii University
python3 manage.py runserver
```

Then open `http://127.0.0.1:8000/map/` (buyers) or `/admin/` after
`python3 manage.py createsuperuser`. Demo farmer logins: `+25470000101…106`,
password `demo-farm-1`.

Front-end build (only needed when templates/styles change):

```bash
cd farmconnect && npm install && npm run build
```

## Status

V1 pilot prototype — open items and decisions are tracked in the design docs
(see `design/`).
