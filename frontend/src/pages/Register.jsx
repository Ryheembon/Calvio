import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { saveToken } from "../auth";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    business_name: "",
    slug: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      if (field === "business_name" && !prev.slugTouched) {
        next.slug = value
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
      }
      if (field === "slug") next.slugTouched = true;
      return next;
    });
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.register({
        business_name: form.business_name,
        slug: form.slug,
        email: form.email,
        password: form.password,
      });
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
        <h1>Create your booking page</h1>
        <p className="muted">Free to start. Share one link with clients.</p>

        <label>
          Business name
          <input
            required
            value={form.business_name}
            onChange={(e) => update("business_name", e.target.value)}
            placeholder="Maya's Cuts"
          />
        </label>

        <label>
          Booking link
          <div className="slug-field">
            <span>/b/</span>
            <input
              required
              value={form.slug}
              onChange={(e) => update("slug", e.target.value)}
              placeholder="mayas-cuts"
            />
          </div>
        </label>

        <label>
          Email
          <input
            required
            type="email"
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
          />
        </label>

        <label>
          Password
          <input
            required
            type="password"
            minLength={6}
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
          />
        </label>

        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" disabled={loading}>
          {loading ? "Creating…" : "Create account"}
        </button>
        <p className="muted center">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
