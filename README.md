# Calvio

Simple booking pages for local service businesses.

Clients pick a time on your public link. You both get a confirmation email.
Built for learning + shipping: **React** frontend + **Python FastAPI** backend.

## Features (v1)

- Create an account and get a public booking link (`/b/your-name`)
- Set weekly hours + appointment length
- Clients book open time slots
- Dashboard shows upcoming appointments and lets you cancel them
- Confirmation + password-reset emails via SMTP (prints to logs if not configured)

## Run locally

### 1. Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend (new terminal)

```bash
cd frontend
npm run dev
```

App: http://127.0.0.1:5173

## First test path

1. Open the app → **Start free**
2. Create a business (example slug: `mayas-cuts`)
3. In the dashboard, set hours + bio
4. Open your public page and book a slot with a test email
5. Check the inbox (or backend logs if SMTP is not set) for confirmation emails

## Project layout

```
backend/app/     Python API (auth, slots, bookings)
frontend/src/    React pages (landing, dashboard, public book page)
```

## Later (scale path)

- SMS reminders
- Deposits / cancellation window
- Multiple staff calendars

## Railway Postgres

SQLite is fine locally. On Railway, add a **Postgres** database so bookings survive redeploys.

1. Railway project → **+ New** → **Database** → **PostgreSQL**
2. Open your **Calvio** service → **Variables**
3. Add / connect `DATABASE_URL` from the Postgres service (Railway can insert `${{Postgres.DATABASE_URL}}`)
4. Redeploy the backend

Health check should then show `"database": "postgres"`:
`https://calvio-production-ff2c.up.railway.app/api/health`

Your old SQLite file on Railway will not copy over — register again after the switch if needed.

## Real email (SMTP)

Easiest beginner option: [Resend](https://resend.com) (free test emails).

1. Create a Resend account → **API Keys** → copy `re_...`
2. Railway → Calvio service → **Variables**:

| Variable | Value |
|----------|--------|
| `SMTP_HOST` | `smtp.resend.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `resend` |
| `SMTP_PASSWORD` | your `re_...` key |
| `EMAIL_FROM` | `Calvio <onboarding@resend.dev>` |

3. Redeploy. Health check should show `"email": true`.

Until you verify your own domain, Resend only sends to **your** Resend account email. That is enough to test booking + password reset.

## Stripe (Calvio Pro — $19/mo)

Businesses can upgrade from the dashboard. Free accounts still work; Pro is optional for now.

### 1. Stripe Dashboard (test mode)

1. Create a Product: **Calvio Pro**
2. Add a recurring price: **$19 / month**
3. Copy the Price ID (`price_...`)
4. Copy your Secret key (`sk_test_...`)

### 2. Railway variables

| Variable | Value |
|----------|--------|
| `STRIPE_SECRET_KEY` | `sk_test_...` |
| `STRIPE_PRICE_ID` | `price_...` |
| `STRIPE_WEBHOOK_SECRET` | from step 3 (`whsec_...`) |
| `FRONTEND_URL` | `https://calvio-three.vercel.app` |

### 3. Webhook

In Stripe → Developers → Webhooks → Add endpoint:

- URL: `https://calvio-production-ff2c.up.railway.app/api/billing/webhook`
- Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`

Copy the signing secret into `STRIPE_WEBHOOK_SECRET`.

### 4. Customer portal (optional but recommended)

Stripe → Settings → Billing → Customer portal → turn on cancel/update payment method.

## Notes

- Local SQLite file is created at `backend/calvio.db`
- On Railway, use Postgres via `DATABASE_URL`
- Change `secret_key` before any real deployment (`backend/app/config.py` or a `.env` file)
- Use Stripe **test mode** until you are ready for real charges
