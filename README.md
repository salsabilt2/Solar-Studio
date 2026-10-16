# Solar Studio

Solar Studio helps a person explore how much electricity solar panels **might** produce at a chosen place. A visitor can compare roof arrangements using past weather, save projects, receive reports, and ask questions grounded in panel documents. All figures are estimates, never measured panel output.

The landing page is a custom, scroll-controlled “One roof. One day” scene. Its sun crosses a drawn roof while a chart reveals hourly electricity from the same Python calculation used by the planner. The story leads into a live trial where visitors can change among three example places, panel direction, slope, and count. The signed-in planner supports locations worldwide. Pointer movement adds depth on desktop; reduced-motion visitors receive the same story as still content.

## Stack

- **API and calculation:** Python, FastAPI, SQLAlchemy, Alembic, pvlib, pandas
- **Data:** PostgreSQL with pgvector in production; SQLite for a quick local start
- **Interface:** React, TypeScript, Vite, Motion, Leaflet, Recharts
- **AI:** OpenAI embeddings for document retrieval and a configurable answer model; answers include PDF page references. Python calculates all proposed changes.
- **Jobs:** idempotent report records and a protected nightly endpoint called by GitHub Actions

The three starting products use their manufacturers' [JinkoSolar](https://www.jinkosolar.com/uploads/JKM420-440N-54HL4R-B-F1.3-EN.pdf), [AIKO](https://aikosolar.com/wp-content/uploads/2024/06/Neostar-2P_188-AIKO-A-MAH54Mw_450-485W_1757x1134x30mm_wbbf_DSDr_EN_2405_V1.5.pdf), and [Qcells](https://us.qcells.com/wp-content/uploads/2023/10/Qcells_Data_sheet_Q.TRON_BLK_M-G2_series_415-440_2023-09_Rev01_NA.pdf) data sheets. Reports keep a copy of their specifications so later catalogue edits do not rewrite old results.

## Run locally

The easiest full-stack start needs Docker:

```sh
docker compose up --build
```

Open `http://localhost:8000`, view test mail at `http://localhost:8025`, and see the API at `http://localhost:8000/docs`. The local Compose file uses PostgreSQL with pgvector and a local mail inbox. It does not send public email.

Without Docker, use Python 3.12–3.14 and Node 22:

```sh
cp .env.example .env
python -m venv .venv
.venv/bin/pip install '.[dev]'
cd frontend && npm ci && npm run build && cd ..
.venv/bin/alembic upgrade head
.venv/bin/uvicorn backend.main:app --reload
```

The default `.env.example` uses SQLite and public local signup. For AI, add `OPENAI_API_KEY`. To send a report, configure Resend (`RESEND_API_KEY`, `EMAIL_FROM`) or a local SMTP host. Without email configuration, reports show a delivery failure and the project remains editable.

## What works

- Accounts, company products, administrator tiers, one-project/three-setup free limits, private projects, project copying, and account deactivation.
- Search worldwide places or pick a map point; select a panel, count, usable roof space, slope, and direction. The app checks that the chosen panels fit the entered space.
- Fetch historical Open-Meteo weather; calculate hourly and daily estimates with pvlib. Missing hours cause a visible error. A one-day to one-year date range is supported within the past year.
- Create and download PDF reports; email each result; lock the whole project only after the provider accepts the email. Failed delivery can be retried.
- Upload private panel PDFs or publish product PDFs as a company. The assistant retrieves relevant passages, cites document pages, and refuses an unsupported answer. Saved report explanations and natural-language “what if” comparisons use the same data and Python calculation.
- Run nightly weather refresh, unfinished report retries, and automatic first reports for setups at least 30 days old through `POST /api/v1/jobs/run-due` with `Authorization: Bearer <SCHEDULER_SECRET>`.

## Calculation notes

Open-Meteo supplies hourly shortwave, direct, and diffuse radiation, temperature, wind, and cloud cover. pvlib determines the sun position and panel-plane irradiance, estimates cell temperature and DC power with PVWatts, then applies the default 14% system loss and an inverter model. The summed hourly values are **kWh**; the rated panel size is **kW**. These are planning estimates and do not include local shade, roof obstructions, snow cover, or a site survey. Reports record the inputs, dates, source, and calculation name. Weather and calculation failures are surfaced to the user.

## Checks

```sh
.venv/bin/ruff check backend tests alembic
.venv/bin/ruff format --check backend tests alembic
.venv/bin/pytest -q
cd frontend && npm run format:check && npm run build
```

CI also applies the migration to a real PostgreSQL/pgvector service. The browser should be checked at mobile, tablet, and desktop widths, including reduced motion.

## Deployment

`render.yaml` provides a free web-service blueprint. Connect a PostgreSQL instance with pgvector, then set `DATABASE_URL`, `PUBLIC_URL`, `INVITE_CODE`, `OPENAI_API_KEY`, and verified email sender settings. Startup runs `alembic upgrade head`. Production refuses to start with open signup or a missing invitation code. Add `SOLAR_STUDIO_URL` and `SOLAR_SCHEDULER_SECRET` as GitHub Actions secrets for the nightly workflow. Render's free service may sleep; the next scheduled run retries saved pending work.

The app reserves estimated AI cost against `AI_MONTHLY_LIMIT_USD` (default $5) and limits non-admin accounts to five AI requests per day. This is an in-app usage gate, **not a provider billing guarantee**; set an account-level spending limit with the AI provider as well. The public showcase is intended for non-commercial use under the weather provider's terms. Email and AI require service credentials before those features work in a public deployment.

## Repository map

`backend/` contains the API, authorization, calculations, reports, and AI. `frontend/src/` contains the landing story and planner. `alembic/` records the database schema. `tests/` covers account boundaries, report locking, calculations, and safe retries. `docs/` contains the [case study](docs/case-study.md) and [AI evaluation guide](docs/ai-evaluation.md).
