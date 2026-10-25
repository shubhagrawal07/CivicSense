import { useState } from "react";

const ACCEPTED_TYPES = ["image/jpeg", "image/png"];
const MAX_SIZE_BYTES = 5 * 1024 * 1024;

interface ImageUploadProps {
  onChange: (file: File | null) => void;
}

export function ImageUpload({ onChange }: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;

    if (!file) {
      setPreview(null);
      setError(null);
      onChange(null);
      return;
    }

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Only JPEG or PNG images are allowed.");
      setPreview(null);
      onChange(null);
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      setError("Image must be 5MB or smaller.");
      setPreview(null);
      onChange(null);
      return;
    }

    setError(null);
    setPreview(URL.createObjectURL(file));
    onChange(file);
  }

  return (
    <div>
      <label htmlFor="report-image">Photo (optional)</label>

      <input
        id="report-image"
        type="file"
        accept="image/jpeg,image/png"
        onChange={handleFileChange}
      />

      {error && <p role="alert">{error}</p>}

      {preview && (
        <img
          src={preview}
          alt="Selected photo preview"
          width={160}
          style={{ display: "block", marginTop: 8 }}
        />
      )}
    </div>
  );
}