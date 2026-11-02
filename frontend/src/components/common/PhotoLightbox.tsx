import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

interface PhotoLightboxProps {
  src: string;
  alt: string;
}

export function PhotoLightbox({ src, alt }: PhotoLightboxProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open]);

  function openPhoto(event: React.MouseEvent) {
    event.stopPropagation();
    setOpen(true);
  }

  function closePhoto(event: React.MouseEvent) {
    event.stopPropagation();
    setOpen(false);
  }

  return (
    <>
      <button type="button" className="photo-thumb" onClick={openPhoto} aria-label="View photo">
        <img src={src} alt={alt} width={48} height={48} />
      </button>
      {open &&
        createPortal(
          <div className="lightbox-backdrop" onClick={closePhoto} role="dialog" aria-modal="true">
            <button type="button" className="lightbox-close" onClick={closePhoto} aria-label="Close">
              ×
            </button>
            <img
              className="lightbox-image"
              src={src}
              alt={alt}
              onClick={(event) => event.stopPropagation()}
            />
          </div>,
          document.body,
        )}
    </>
  );
}
