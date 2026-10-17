const KEY = "authToken";

// storage can throw in private windows or when site data is blocked
export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function storeToken(token: string): void {
  try {
    localStorage.setItem(KEY, token);
  } catch {
    // the session just will not survive a refresh
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // nothing to clear
  }
}
