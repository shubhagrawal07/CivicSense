import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="landing">
      <h1>CivicSense</h1>
      <p className="landing-tagline">Report a problem in your city and see it reach the right people.</p>

      <p>
        Potholes, broken streetlights, garbage and water leaks often go unnoticed because nobody
        knows who should fix them. CivicSense lets a citizen report a problem with a short
        description, a photo and a location on the map.
      </p>

      <h2>How it works</h2>
      <ol>
        <li>You submit a report with text, a photo and a pin on the map.</li>
        <li>The system works out the category and how serious the problem is.</li>
        <li>Reports about the same problem are grouped into one issue.</li>
        <li>The issue is matched to the responsible authority and its official contact.</li>
      </ol>

      <p>
        Everyone can explore the dashboard, the issue map and the ward map to see where problems
        are piling up. Log in to submit your own report.
      </p>

      <div className="button-row">
        <Link to="/report/new" className="nav-button">
          Report an issue
        </Link>
        <Link to="/dashboard" className="nav-button">
          View dashboard
        </Link>
      </div>
    </div>
  );
}
