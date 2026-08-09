# Calvio

Simple booking pages for local service businesses.

Clients pick a time on your public link. You both get a confirmation email.
Built for learning + shipping: **React** frontend + **Python FastAPI** backend.

## Features (v1)

- Create an account and get a public booking link (`/b/your-name`)
- Set weekly hours + appointment length
- Clients book open time slots
- Dashboard shows upcoming appointments
- Emails print in the backend terminal (SMTP optional later)

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
5. Check the backend terminal for the confirmation “emails”

## Project layout

```
backend/app/     Python API (auth, slots, bookings)
frontend/src/    React pages (landing, dashboard, public book page)
```

## Later (scale path)

- Stripe subscriptions ($19/mo)
- SMS reminders
- Deposits / cancellation window
- Multiple staff calendars

## Notes

- SQLite database file is created at `backend/calvio.db`
- Change `secret_key` before any real deployment (`backend/app/config.py` or a `.env` file)
