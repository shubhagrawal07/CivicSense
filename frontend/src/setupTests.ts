import "@testing-library/jest-dom/vitest";

// jsdom does not implement these; ImageUpload's preview relies on them.
URL.createObjectURL = URL.createObjectURL ?? (() => "blob:mock-url");
URL.revokeObjectURL = URL.revokeObjectURL ?? (() => {});
