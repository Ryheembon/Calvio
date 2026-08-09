import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, formatWhen, minutesToTime, timeToMinutes } from "../api";
import { clearToken } from "../auth";

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Dashboard() {
  const navigate = useNavigate();
  const [me, setMe] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [bio, setBio] = useState("");
  const [slotMinutes, setSlotMinutes] = useState(30);
  const [availability, setAvailability] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [profile, appts] = await Promise.all([api.me(), api.appointments()]);
        setMe(profile);
        setBio(profile.bio || "");
        setSlotMinutes(profile.slot_minutes);
        setAvailability(profile.availability);
        setAppointments(appts);
      } catch (err) {
        clearToken();
        navigate("/login");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [navigate]);

  function updateDay(day, patch) {
    setAvailability((prev) =>
      prev.map((row) => (row.day_of_week === day ? { ...row, ...patch } : row)),
    );
  }

  async function saveProfile(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const updated = await api.updateMe({ bio, slot_minutes: Number(slotMinutes) });
      setMe(updated);
      setMessage("Profile saved.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function saveHours(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const updated = await api.updateAvailability(availability);
      setMe(updated);
      setAvailability(updated.availability);
      setMessage("Hours saved.");
    } catch (err) {
      setError(err.message);
    }
  }

  function logout() {
    clearToken();
    navigate("/");
  }

  if (loading) {
    return (
      <div className="page">
        <p className="muted">Loading dashboard…</p>
      </div>
    );
  }

  const bookingUrl = `${window.location.origin}/b/${me.slug}`;
  const upcoming = appointments.filter((a) => new Date(a.starts_at) >= new Date());

  return (
    <div className="page dashboard">
      <header className="topbar">
        <Link to="/" className="brand">
          Calvio
        </Link>
        <div className="top-actions">
          <a className="text-link" href={bookingUrl} target="_blank" rel="noreferrer">
            View public page
          </a>
          <button type="button" className="btn btn-ghost" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      <section className="dash-hero">
        <div>
          <p className="eyebrow">Your booking page</p>
          <h1>{me.business_name}</h1>
          <p className="share-line">
            Share this link: <a href={bookingUrl}>{bookingUrl}</a>
          </p>
        </div>
      </section>

      {(message || error) && (
        <p className={error ? "error banner" : "success banner"}>{error || message}</p>
      )}

      <div className="dash-grid">
        <section className="panel">
          <h2>Upcoming appointments</h2>
          {upcoming.length === 0 ? (
            <p className="muted">No bookings yet. Share your link to get your first one.</p>
          ) : (
            <ul className="appt-list">
              {upcoming.map((appt) => (
                <li key={appt.id}>
                  <strong>{appt.client_name}</strong>
                  <span>{formatWhen(appt.starts_at)}</span>
                  <span className="muted">{appt.client_email}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel">
          <h2>Profile</h2>
          <form onSubmit={saveProfile} className="stack-form">
            <label>
              Short bio
              <textarea
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Haircuts, fades, and beard trims downtown."
              />
            </label>
            <label>
              Appointment length (minutes)
              <select value={slotMinutes} onChange={(e) => setSlotMinutes(e.target.value)}>
                {[15, 30, 45, 60, 90].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn btn-primary">Save profile</button>
          </form>
        </section>

        <section className="panel panel-wide">
          <h2>Weekly hours</h2>
          <form onSubmit={saveHours} className="hours-form">
            {availability.map((row) => (
              <div className="hours-row" key={row.day_of_week}>
                <label className="day-toggle">
                  <input
                    type="checkbox"
                    checked={row.is_open}
                    onChange={(e) => updateDay(row.day_of_week, { is_open: e.target.checked })}
                  />
                  {DAY_NAMES[row.day_of_week]}
                </label>
                <input
                  type="time"
                  disabled={!row.is_open}
                  value={minutesToTime(row.start_minute)}
                  onChange={(e) =>
                    updateDay(row.day_of_week, { start_minute: timeToMinutes(e.target.value) })
                  }
                />
                <span>to</span>
                <input
                  type="time"
                  disabled={!row.is_open}
                  value={minutesToTime(row.end_minute)}
                  onChange={(e) =>
                    updateDay(row.day_of_week, { end_minute: timeToMinutes(e.target.value) })
                  }
                />
              </div>
            ))}
            <button className="btn btn-primary">Save hours</button>
          </form>
        </section>
      </div>
    </div>
  );
}
