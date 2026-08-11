import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!token) {
      setError("Missing reset token. Request a new link.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const data = await api.resetPassword({ token, password });
      setMessage(data.message);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page auth-page">
      <Link to="/" className="brand">
        Calvio
      </Link>
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Choose a new password</h1>
        <p className="muted">Pick something you’ll remember (at least 6 characters).</p>

        <label>
          New password
          <input
            required
            type="password"
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        <label>
          Confirm password
          <input
            required
            type="password"
            minLength={6}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
        </label>

        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}

        <button className="btn btn-primary" disabled={loading || !token}>
          {loading ? "Saving…" : "Update password"}
        </button>
        <p className="muted center">
          <Link to="/forgot-password">Request a new link</Link>
        </p>
      </form>
    </div>
  );
}
