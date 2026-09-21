# MONEA — Personal Finance OS

A private, premium personal money manager. Run it locally. There is no multi-tenant SaaS layer, no bank login, and no investment advice.

## Stack

- Backend: Python, Django, Django REST Framework, SQLite (PostgreSQL-ready via `DATABASE_URL`)
- Frontend: React, TypeScript, Vite, Tailwind CSS
- Money: `Decimal` only. Transfers never count as expenses.

## Quick start

From the project root (`Money Manager`):

### 1. Environment

```powershell
copy .env.example .env
```

Edit `.env` and set a real `SECRET_KEY` before using this with real money.

### 2. Backend

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
cd backend
python manage.py migrate
python manage.py seed_demo --reset
python manage.py runserver
```

This creates an empty workspace for **Ahsan Nadeem** (no sample transactions). Set `OWNER_USERNAME` and `OWNER_PASSWORD` in `.env` first.

If the database is empty, the first visit to the app also offers a one-time workspace registration.

### 3. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite dev server proxies `/api` to Django on port 8000.

## Useful commands

| Task | Command |
| --- | --- |
| Migrate | `python backend/manage.py migrate` |
| Seed empty workspace | `python backend/manage.py seed_demo --reset` |
| Tests | `python backend/manage.py test` |
| Django admin | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |
| Frontend build | `cd frontend && npm run build` |

## Environment variables

See `.env.example`.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret |
| `DEBUG` | `true` for local development |
| `DATABASE_URL` | Empty = SQLite. Postgres example: `postgres://USER:PASSWORD@HOST:5432/monea` |
| `CORS_ALLOWED_ORIGINS` | Frontend origins |
| `DEFAULT_CURRENCY` | Default `PKR` |
| `AI_API_KEY` | Groq (or other OpenAI-compatible) key for the assistant |
| `AI_API_BASE` | Default `https://api.groq.com/openai/v1` |
| `AI_MODEL` | Default `openai/gpt-oss-20b` |
| `OCR_PROVIDER` | `none` or `tesseract` |

## Deploy on Vercel

The GitHub repo deploys the React app and the Django API on the same Vercel project.

1. Push to `main`.
2. Import the repo in Vercel (root directory = repository root).
3. Set environment variables in the Vercel project:
   - `SECRET_KEY`
   - `DEBUG=false`
   - `DATABASE_URL` (Neon or Vercel Postgres — SQLite will not persist on Vercel)
   - `AI_API_KEY` (Groq)
   - `AI_API_BASE=https://api.groq.com/openai/v1`
   - `AI_MODEL=openai/gpt-oss-20b`
   - `ALLOWED_HOSTS=.vercel.app,localhost`
   - `CORS_ALLOWED_ORIGINS=https://<your-app>.vercel.app`
4. After the first deploy, run migrations against that database:
   `python backend/manage.py migrate` (locally with `DATABASE_URL` pointing at Neon, or a one-off).

Until `DATABASE_URL` is set, the API cannot store money records in production.

## What is implemented

- Authentication, password change, optional PIN lock, PWA install
- Accounts, categories, transactions, receipts, natural-language entry
- Transfers that do not count as spending
- Budgets with projected spend and written insights
- Savings goals and contributions
- Bills, calendar, subscriptions
- Debts, lending / borrowing
- Investments (manual records only)
- Dashboard with total balance and configurable Safe-to-Spend
- Analytics, yearly review, net worth history
- CSV / Excel import wizard, CSV / Excel / PDF export, JSON backup + restore
- Notifications, calculators, local AI assistant (database-backed, no invented numbers)
- Light / dark / system theme, mobile bottom nav, desktop sidebar

## Money rules

- Amounts are stored as `Decimal`, never `float`
- Income / expense totals ignore transfers
- Paying a credit card is a transfer into the card account, not a second expense
- Deleting or recategorizing a transaction updates balances and analytics
- Safe-to-Spend is: available cash − upcoming bills − debt payments − reserved goals − emergency reserve − savings reserve (each term is configurable in Settings)

## Remaining optional work

- Live currency feeds (architecture is ready; rates are manual)
- Tesseract-backed receipt OCR (`OCR_PROVIDER=tesseract` plus system Tesseract)
- Cloud LLM via Groq when `AI_API_KEY` is set (answers are grounded in your database; the local engine is the fallback)
- Platform WebAuthn biometrics beyond PIN + PWA standalone mode

## Privacy

Do not log balances in the browser console. Passwords use Django’s hasher. PIN values are hashed. Keep `.env` out of git.
