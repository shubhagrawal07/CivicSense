import { useState } from "react";
import { submitReport } from "../../api/reports";
import { ErrorBanner } from "../common/ErrorBanner";
import { ImageUpload } from "./ImageUpload";
import { LocationPicker, type LatLng } from "./LocationPicker";

interface ReportFormProps {
  onSubmitted: (reportId: string) => void;
}

interface FieldErrors {
  [field: string]: string;
}

export function ReportForm({ onSubmitted }: ReportFormProps) {
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [location, setLocation] = useState<LatLng | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    setFieldErrors({});

    if (!description.trim() && !image) {
      setFieldErrors({
        description: "Add a description, a photo, or both.",
      });
      return;
    }

    if (!location) {
      setFormError("Pick a location on the map before submitting.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await submitReport({
        description: description.trim() || undefined,
        image,
        latitude: location.lat,
        longitude: location.lng,
      });
      onSubmitted(response.id);
    } catch (err) {
      const apiError = err as {
        status?: number;
        errors?: { field: string; message: string }[];
        message?: string;
      };
      if (apiError.status === 422 && apiError.errors) {
        const mapped: FieldErrors = {};
        for (const fieldError of apiError.errors) {
          mapped[fieldError.field] = fieldError.message;
        }
        setFieldErrors(mapped);
      } else {
        setFormError(apiError.message ?? "Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <p>Add a description, a photo, or both.</p>

      <div className="field">
        <label htmlFor="report-description">Description (optional)</label>
        <textarea
          id="report-description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        {fieldErrors.description && <p role="alert">{fieldErrors.description}</p>}
      </div>

      <div className="field">
        <ImageUpload onChange={setImage} />
      </div>

      <div className="field">
        <LocationPicker value={location} onChange={setLocation} />
      </div>

      {formError && <ErrorBanner message={formError} />}

      <button type="submit" disabled={submitting}>
        {submitting ? "Submitting…" : "Submit report"}
      </button>
    </form>
  );
}
