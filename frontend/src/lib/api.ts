// Default: mesma origem (frontend servido pelo FastAPI).
// Em dev local: setar NEXT_PUBLIC_API_URL=http://localhost:8000
const BASE = process.env.NEXT_PUBLIC_API_URL || "";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

export async function api<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  // Todas as chamadas vão pra /api/* (FastAPI serve o frontend na raiz)
  const url = `${BASE}/api${path.startsWith("/") ? "" : "/"}${path}`;
  const r = await fetch(url, { ...init, headers });
  if (!r.ok) {
    const erro = await r.text();
    throw new Error(erro || `HTTP ${r.status}`);
  }
  if (r.status === 204) return undefined as T;
  return r.json();
}
