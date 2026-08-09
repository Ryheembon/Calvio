import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatWhen } from "../api";

function toDayInputValue(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export default function PublicBook() {
  const { slug } = useParams();
  const today = useMemo(() => toDayInputValue(new Date()), []);
  const [business, setBusiness] = useState(null);
  const [day, setDay] = useState(today);
  const [slots, setSlots] = useState([]);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ client_name: "", client_email: "", notes: "" });
  const [done, setDone] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    async function loadBusiness() {
      setError("");
      try {
        const data = await api.publicBusiness(slug);
        setBusiness(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadBusiness();
  }, [slug]);

  useEffect(() => {
    async function loadSlots() {
      if (!business) return;
      setSelected(null);
      try {
        const data = await api.publicSlots(slug, day);
        setSlots(data);
      } catch (err) {
        setError(err.message);
      }
    }
    loadSlots();
  }, [business, slug, day]);

  async function onBook(event) {
    event.preventDefault();
    if (!selected) return;
    setBooking(true);
    setError("");
    try {
      const appt = await api.book(slug, {
        ...form,
        starts_at: selected,
      });
      setDone(appt);
    } catch (err) {
      setError(err.message);
    } finally {
      setBooking(false);
    }
  }

  if (loading) {
    return (
      <div className="page public-page">
        <p className="muted">Loading booking page…</p>
      </div>
    );
  }

  if (!business) {
    return (
      <div className="page public-page">
        <h1>Page not found</h1>
        <p className="muted">{error || "This booking link doesn’t exist."}</p>
        <Link to="/">Go home</Link>
      </div>
    );
  }

  if (done) {
    return (
      <div className="page public-page">
        <div className="book-shell success-shell">
          <p className="eyebrow">You’re booked</p>
          <h1>{business.business_name}</h1>
          <p>
            See you {formatWhen(done.starts_at)}. A confirmation email was sent to{" "}
            <strong>{done.client_email}</strong>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page public-page">
      <div className="book-shell">
        <header className="book-header">
          <p className="eyebrow">Book with</p>
          <h1>{business.business_name}</h1>
          {business.bio && <p className="lede">{business.bio}</p>}
          <p className="muted">{business.slot_minutes}-minute appointments</p>
        </header>

        <label className="day-picker">
          Pick a day
          <input type="date" min={today} value={day} onChange={(e) => setDay(e.target.value)} />
        </label>

        <div className="slot-grid">
          {slots.length === 0 ? (
            <p className="muted">No open times this day. Try another date.</p>
          ) : (
            slots.map((slot) => {
              const active = selected === slot.starts_at;
              return (
                <button
                  key={slot.starts_at}
                  type="button"
                  className={`slot-btn ${active ? "active" : ""}`}
                  onClick={() => setSelected(slot.starts_at)}
                >
                  {new Date(slot.starts_at).toLocaleTimeString(undefined, {
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </button>
              );
            })
          )}
        </div>

        {selected && (
          <form className="stack-form book-form" onSubmit={onBook}>
            <h2>Your details</h2>
            <p className="muted">Selected: {formatWhen(selected)}</p>
            <label>
              Name
              <input
                required
                value={form.client_name}
                onChange={(e) => setForm({ ...form, client_name: e.target.value })}
              />
            </label>
            <label>
              Email
              <input
                required
                type="email"
                value={form.client_email}
                onChange={(e) => setForm({ ...form, client_email: e.target.value })}
              />
            </label>
            <label>
              Notes (optional)
              <textarea
                rows={3}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </label>
            {error && <p className="error">{error}</p>}
            <button className="btn btn-primary" disabled={booking}>
              {booking ? "Booking…" : "Confirm booking"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
