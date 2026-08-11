import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [resetUrl, setResetUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setResetUrl("");
    setLoading(true);
    try {
      const data = await api.forgotPassword({ email });
      setMessage(data.message);
      if (data.reset_url) setResetUrl(data.reset_url);
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
        <h1>Forgot password</h1>
        <p className="muted">Enter your account email and we’ll send a reset link.</p>

        <label>
          Email
          <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>

        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}
        {resetUrl && (
          <p className="success">
            Email isn’t configured yet, so use this link:{" "}
            <a href={resetUrl}>Reset password</a>
          </p>
        )}

        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Sending…" : "Send reset link"}
        </button>
        <p className="muted center">
          <Link to="/login">Back to log in</Link>
        </p>
      </form>
    </div>
  );
}
