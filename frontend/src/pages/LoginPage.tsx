import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { parseApiError } from "../api/errors";
import { destinationFrom } from "../auth/redirect";
import { useAuth } from "../auth/AuthContext";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { FormField } from "../components/common/FormField";

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const destination = destinationFrom(location.state);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to={destination} replace />;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    const problems: Record<string, string> = {};
    if (!EMAIL_PATTERN.test(email.trim())) problems.email = "Enter a valid email address.";
    if (!password) problems.password = "Enter your password.";
    setFieldErrors(problems);
    if (Object.keys(problems).length > 0) return;

    setSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      navigate(destination, { replace: true });
    } catch (err) {
      const parsed = parseApiError(err);
      setFieldErrors(parsed.fieldErrors);
      if (Object.keys(parsed.fieldErrors).length === 0) setFormError(parsed.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Log in</h1>
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={setEmail}
          error={fieldErrors.email}
        />
        <FormField
          id="password"
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
          error={fieldErrors.password}
        />
        {formError && <ErrorBanner message={formError} />}
        <button type="submit" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p>
        New here? <Link to="/register">Create an account</Link>
      </p>
    </div>
  );
}
