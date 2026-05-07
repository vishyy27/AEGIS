const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const requestCache = new Map<string, Promise<any>>();

export async function fetchAPI<T = unknown>(path: string, options?: RequestInit & { skipCache?: boolean; retries?: number }): Promise<T> {
  const url = `${API}${path}`;
  const method = options?.method || "GET";
  const cacheKey = `${method}:${url}`;

  if (method === "GET" && !options?.skipCache && requestCache.has(cacheKey)) {
    return requestCache.get(cacheKey) as Promise<T>;
  }

  const retries = options?.retries ?? 2;

  const execute = async (attempt: number): Promise<T> => {
    try {
      const res = await fetch(url, {
        headers: { "Content-Type": "application/json", ...options?.headers },
        ...options,
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return await res.json();
    } catch (err) {
      if (attempt < retries) {
        await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
        return execute(attempt + 1);
      }
      throw err;
    }
  };

  const promise = execute(0).finally(() => {
    if (method === "GET" && requestCache.get(cacheKey) === promise) {
      // Keep cache for 30s to prevent duplicate dashboard mounts from refetching
      setTimeout(() => requestCache.delete(cacheKey), 30000);
    }
  });

  if (method === "GET" && !options?.skipCache) {
    requestCache.set(cacheKey, promise);
  }

  return promise;
}

export function getWSUrl(topics?: string[]): string {
  const base = API.replace("http", "ws");
  const params = topics && topics.length > 0 ? `?topics=${topics.join(",")}` : "";
  return `${base}/ws/telemetry${params}`;
}

export { API };
