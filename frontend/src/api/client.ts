const ACCESS = "monea.access";
const REFRESH = "monea.refresh";
const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

function endpoint(path: string) {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

type Options = RequestInit & { skipAuth?: boolean };

async function raw(path: string, options: Options = {}) {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = localStorage.getItem(ACCESS);
  if (token && !options.skipAuth) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(endpoint(path), { ...options, headers });
  if (response.status === 401 && !options.skipAuth) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${localStorage.getItem(ACCESS)}`);
      return fetch(endpoint(path), { ...options, headers });
    }
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
    headers.delete("Authorization");
    return fetch(endpoint(path), { ...options, headers });
  }
  return response;
}

async function tryRefresh() {
  const refresh = localStorage.getItem(REFRESH);
  if (!refresh) return false;
  const response = await fetch(endpoint("/api/auth/refresh/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
    return false;
  }
  const data = await response.json();
  localStorage.setItem(ACCESS, data.access);
  if (data.refresh) localStorage.setItem(REFRESH, data.refresh);
  return true;
}

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const response = await raw(path, options);
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.error || "Something went wrong. Please try again.") as Error & {
      fields?: Record<string, string[]>;
      status: number;
    };
    error.fields = data.fields;
    error.status = response.status;
    throw error;
  }
  return data as T;
}

export async function apiBlob(path: string) {
  const response = await raw(path);
  if (!response.ok) throw new Error("Could not download the file.");
  return response.blob();
}

export const tokens = {
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS, access);
    localStorage.setItem(REFRESH, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
  access() {
    return localStorage.getItem(ACCESS);
  },
};

export async function flushOfflineQueue() {
  const rawQueue = localStorage.getItem("monea.offline-queue");
  if (!rawQueue) return;
  const items = JSON.parse(rawQueue) as unknown[];
  const remaining: unknown[] = [];
  for (const item of items) {
    try {
      await api("/api/transactions/", { method: "POST", body: JSON.stringify(item) });
    } catch {
      remaining.push(item);
    }
  }
  if (remaining.length) localStorage.setItem("monea.offline-queue", JSON.stringify(remaining));
  else localStorage.removeItem("monea.offline-queue");
}

export function enqueueTransaction(payload: unknown) {
  const rawQueue = localStorage.getItem("monea.offline-queue");
  const items = rawQueue ? JSON.parse(rawQueue) : [];
  items.push(payload);
  localStorage.setItem("monea.offline-queue", JSON.stringify(items));
}
