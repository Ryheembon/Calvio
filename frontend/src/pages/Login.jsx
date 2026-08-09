import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { saveToken } from "../auth";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.login({ email, password });
      saveToken(data.access_token);
      navigate("/dashboard");
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
        <h1>Welcome back</h1>
        <p className="muted">Log in to manage your bookings.</p>

        <label>
          Email
          <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>

        <label>
          Password
          <input
            required
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Logging in…" : "Log in"}
        </button>
        <p className="muted center">
          New here? <Link to="/register">Create a booking page</Link>
        </p>
      </form>
    </div>
  );
}
