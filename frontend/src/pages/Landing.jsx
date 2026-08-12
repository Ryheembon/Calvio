import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="landing">
      <section className="landing-hero">
        <div className="landing-hero-media" aria-hidden="true" />
        <div className="landing-hero-veil" aria-hidden="true" />
        <div className="landing-hero-glow" aria-hidden="true" />

        <div className="landing-hero-inner">
          <header className="topbar landing-topbar">
            <Link to="/" className="brand brand-on-dark">
              Calvio
            </Link>
            <nav className="top-actions">
              <Link to="/login" className="text-link text-link-on-dark">
                Log in
              </Link>
              <Link to="/register" className="btn btn-accent">
                Start free
              </Link>
            </nav>
          </header>

          <main className="hero-copy">
            <p className="brand-mark brand-mark-hero">Calvio</p>
            <h1 className="hero-title">Booked before they leave the chair.</h1>
            <p className="lede lede-on-dark">
              One link for your shop. Clients pick a time. You both get the confirmation.
            </p>
            <div className="cta-row">
              <Link to="/register" className="btn btn-accent btn-lg">
                Create your booking page
              </Link>
              <a className="text-link text-link-on-dark" href="#how">
                See how it works
              </a>
            </div>
          </main>
        </div>
      </section>

      <section id="how" className="how">
        <div className="how-inner">
          <p className="eyebrow">Simple by design</p>
          <h2>One job: get booked.</h2>
          <p className="how-lede">Set your hours, share your link, show up to confirmed appointments.</p>
          <ol className="steps">
            <li style={{ "--step": 1 }}>
              <span>01</span>
              <div>
                <strong>Make your page</strong>
                <p>Name, hours, and appointment length — done in minutes.</p>
              </div>
            </li>
            <li style={{ "--step": 2 }}>
              <span>02</span>
              <div>
                <strong>Share your link</strong>
                <p>Send calvio.app/b/your-name on Instagram, texts, or your site.</p>
              </div>
            </li>
            <li style={{ "--step": 3 }}>
              <span>03</span>
              <div>
                <strong>Get the booking</strong>
                <p>Open slots, confirmations, and a clear list of who is coming in.</p>
              </div>
            </li>
          </ol>
          <div className="how-cta">
            <Link to="/register" className="btn btn-primary btn-lg">
              Start free
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
