import "@testing-library/jest-dom/vitest";

URL.createObjectURL = URL.createObjectURL ?? (() => "blob:mock-url");
URL.revokeObjectURL = URL.revokeObjectURL ?? (() => { });
