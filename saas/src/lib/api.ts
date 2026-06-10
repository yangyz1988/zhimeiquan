const API_URL = process.env.API_URL || "http://localhost:8000";
const API_SECRET = process.env.API_SECRET || "";

type FetchOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  cache?: RequestCache;
};

export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {}
): Promise<{ ok: boolean; status: number; data: T }> {
  const { method = "GET", body, headers = {}, cache } = options;

  const fetchHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };
  if (API_SECRET) {
    fetchHeaders["X-API-Key"] = API_SECRET;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: fetchHeaders,
    body: body ? JSON.stringify(body) : undefined,
    cache,
  });

  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}
