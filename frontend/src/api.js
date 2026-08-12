const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function authHeaders() {
  const token = localStorage.getItem("calvio_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(", ")
      : detail || "Request failed";
    throw new Error(message);
  }

  return data;
}

export const api = {
  register: (body) => request("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => request("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  forgotPassword: (body) =>
    request("/api/auth/forgot-password", { method: "POST", body: JSON.stringify(body) }),
  resetPassword: (body) =>
    request("/api/auth/reset-password", { method: "POST", body: JSON.stringify(body) }),
  changePassword: (body) =>
    request("/api/me/change-password", { method: "POST", body: JSON.stringify(body) }),
  me: () => request("/api/me"),
  updateMe: (body) => request("/api/me", { method: "PUT", body: JSON.stringify(body) }),
  updateAvailability: (body) =>
    request("/api/me/availability", { method: "PUT", body: JSON.stringify(body) }),
  appointments: () => request("/api/me/appointments"),
  cancelAppointment: (id) =>
    request(`/api/me/appointments/${id}/cancel`, { method: "POST" }),
  createCheckout: () => request("/api/billing/checkout", { method: "POST" }),
  createPortal: () => request("/api/billing/portal", { method: "POST" }),
  publicBusiness: (slug) => request(`/api/public/${slug}`),
  publicSlots: (slug, day) => request(`/api/public/${slug}/slots?day=${day}`),
  book: (slug, body) =>
    request(`/api/public/${slug}/book`, { method: "POST", body: JSON.stringify(body) }),
};

export function minutesToTime(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function timeToMinutes(value) {
  const [h, m] = value.split(":").map(Number);
  return h * 60 + m;
}

export function formatWhen(iso) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
