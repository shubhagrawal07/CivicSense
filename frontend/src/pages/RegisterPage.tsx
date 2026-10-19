import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { register } from "../api/auth";
import { parseApiError } from "../api/errors";
import { destinationFrom } from "../auth/redirect";
import { useAuth } from "../auth/AuthContext";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { FormField } from "../components/common/FormField";

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;
const MIN_PASSWORD_LENGTH = 8;

export function RegisterPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const destination = destinationFrom(location.state);

  const [name, setName] = useState("");
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
    if (!name.trim()) problems.name = "Enter your name.";
    if (!EMAIL_PATTERN.test(email.trim())) problems.email = "Enter a valid email address.";
    if (password.length < MIN_PASSWORD_LENGTH) {
      problems.password = `Use at least ${MIN_PASSWORD_LENGTH} characters.`;
    }
    setFieldErrors(problems);
    if (Object.keys(problems).length > 0) return;

    setSubmitting(true);
    try {
      await register({ name: name.trim(), email: email.trim(), password });
    } catch (err) {
      const parsed = parseApiError(err);
      if (parsed.status === 409) {
        setFieldErrors({ email: parsed.message });
      } else {
        setFieldErrors(parsed.fieldErrors);
        if (Object.keys(parsed.fieldErrors).length === 0) setFormError(parsed.message);
      }
      setSubmitting(false);
      return;
    }

    try {
      await login({ email: email.trim(), password });
      navigate(destination, { replace: true });
    } catch {
      navigate("/login", { replace: true, state: location.state });
    }
  }

  return (
    <div>
      <h1>Create an account</h1>
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          id="name"
          label="Name"
          autoComplete="name"
          value={name}
          onChange={setName}
          error={fieldErrors.name}
        />
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
          autoComplete="new-password"
          value={password}
          onChange={setPassword}
          error={fieldErrors.password}
        />
        {formError && <ErrorBanner message={formError} />}
        <button type="submit" disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
