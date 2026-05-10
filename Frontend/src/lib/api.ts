const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchAPI<T = unknown>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API}${path}`;
  
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return await res.json();
}

export function getWSUrl(topics?: string[]): string {
  const base = API.replace("http", "ws");
  const params = topics && topics.length > 0 ? `?topics=${topics.join(",")}` : "";
  return `${base}/ws/telemetry${params}`;
}

export { API };
