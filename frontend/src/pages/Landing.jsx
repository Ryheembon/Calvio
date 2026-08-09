import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="page landing">
      <div className="landing-bg" aria-hidden="true" />
      <header className="topbar">
        <Link to="/" className="brand">
          Calvio
        </Link>
        <nav className="top-actions">
          <Link to="/login" className="text-link">
            Log in
          </Link>
          <Link to="/register" className="btn btn-primary">
            Start free
          </Link>
        </nav>
      </header>

      <main className="hero">
        <p className="brand-mark">Calvio</p>
        <h1>A booking page clients can actually use.</h1>
        <p className="lede">
          Share one link. Let people pick a time. Get email confirmations — without chasing texts all day.
        </p>
        <div className="cta-row">
          <Link to="/register" className="btn btn-primary btn-lg">
            Create your booking page
          </Link>
          <a className="text-link" href="#how">
            See how it works
          </a>
        </div>
      </main>

      <section id="how" className="how">
        <h2>One job: get booked.</h2>
        <p>Set your hours, share your link, show up to confirmed appointments.</p>
        <ol className="steps">
          <li>
            <span>01</span>
            Make your page in minutes
          </li>
          <li>
            <span>02</span>
            Share calvio.local/b/you
          </li>
          <li>
            <span>03</span>
            Get bookings + email alerts
          </li>
        </ol>
      </section>
    </div>
  );
}
