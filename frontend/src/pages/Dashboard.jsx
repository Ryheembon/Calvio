import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, formatWhen, minutesToTime, timeToMinutes } from "../api";
import { clearToken } from "../auth";

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Dashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [me, setMe] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [bio, setBio] = useState("");
  const [slotMinutes, setSlotMinutes] = useState(30);
  const [availability, setAvailability] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [billingBusy, setBillingBusy] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [cancelingId, setCancelingId] = useState(null);

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

  useEffect(() => {
    const billing = searchParams.get("billing");
    if (!billing) return;
    if (billing === "success") {
      setMessage("Payment received. Calvio Pro will show as active in a few seconds.");
      api.me().then(setMe).catch(() => {});
    } else if (billing === "cancel") {
      setError("Checkout canceled. You can upgrade anytime.");
    }
    setSearchParams({}, { replace: true });
  }, [searchParams, setSearchParams]);

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

  async function startCheckout() {
    setError("");
    setMessage("");
    setBillingBusy(true);
    try {
      const { url } = await api.createCheckout();
      window.location.href = url;
    } catch (err) {
      setError(err.message);
      setBillingBusy(false);
    }
  }

  async function openPortal() {
    setError("");
    setMessage("");
    setBillingBusy(true);
    try {
      const { url } = await api.createPortal();
      window.location.href = url;
    } catch (err) {
      setError(err.message);
      setBillingBusy(false);
    }
  }

  async function changePassword(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    setPasswordBusy(true);
    try {
      const data = await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMessage(data.message);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setPasswordBusy(false);
    }
  }

  async function cancelAppointment(appt) {
    const when = formatWhen(appt.starts_at);
    if (!window.confirm(`Cancel ${appt.client_name}'s booking on ${when}?`)) {
      return;
    }
    setError("");
    setMessage("");
    setCancelingId(appt.id);
    try {
      const updated = await api.cancelAppointment(appt.id);
      setAppointments((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
      setMessage(`Canceled ${appt.client_name}'s booking.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setCancelingId(null);
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
  const upcoming = appointments.filter(
    (a) => a.status !== "canceled" && new Date(a.starts_at) >= new Date(),
  );
  const isPro = Boolean(me.is_pro);

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
          <h1>
            {me.business_name}
            {isPro ? <span className="pro-badge">Pro</span> : null}
          </h1>
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
          <h2>Plan</h2>
          {isPro ? (
            <>
              <p>You are on <strong>Calvio Pro</strong> ($19/mo).</p>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={billingBusy}
                onClick={openPortal}
              >
                {billingBusy ? "Opening…" : "Manage billing"}
              </button>
            </>
          ) : (
            <>
              <p>
                Free plan: <strong>{me.bookings_used || 0}</strong> of{" "}
                <strong>{me.bookings_limit || 2}</strong> bookings used.
              </p>
              <p className="muted">
                {me.bookings_remaining === 0
                  ? "You've used both free bookings. Upgrade to keep taking appointments."
                  : `${me.bookings_remaining} free booking${me.bookings_remaining === 1 ? "" : "s"} left, then Pro is required.`}
              </p>
              <button
                type="button"
                className="btn btn-primary"
                disabled={billingBusy}
                onClick={startCheckout}
              >
                {billingBusy ? "Redirecting…" : "Upgrade to Pro — $19/mo"}
              </button>
            </>
          )}
        </section>

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
                  {appt.notes ? <span className="appt-notes">Note: {appt.notes}</span> : null}
                  <button
                    type="button"
                    className="btn btn-ghost btn-small"
                    disabled={cancelingId === appt.id}
                    onClick={() => cancelAppointment(appt)}
                  >
                    {cancelingId === appt.id ? "Canceling…" : "Cancel"}
                  </button>
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
                placeholder="What you offer and where clients can find you."
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

        <section className="panel">
          <h2>Change password</h2>
          <form onSubmit={changePassword} className="stack-form">
            <label>
              Current password
              <input
                required
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </label>
            <label>
              New password
              <input
                required
                type="password"
                minLength={6}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </label>
            <label>
              Confirm new password
              <input
                required
                type="password"
                minLength={6}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </label>
            <button className="btn btn-primary" disabled={passwordBusy}>
              {passwordBusy ? "Saving…" : "Update password"}
            </button>
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
