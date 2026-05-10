import { useOrganizationStore } from "@/store/organizationStore";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchAPI<T = unknown>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API}${path}`;
  const orgId = useOrganizationStore.getState().currentOrg?.id;
  
  const headers: Record<string, string> = { 
    "Content-Type": "application/json", 
    ...options?.headers as any 
  };
  
  if (orgId) {
    headers["X-Organization-ID"] = orgId;
  }
  
  const res = await fetch(url, {
    headers,
    ...options,
  });
  
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return await res.json();
}

export function getWSUrl(topics?: string[], orgId?: string): string {
  const base = API.replace("http", "ws");
  const topicParam = topics && topics.length > 0 ? `topics=${topics.join(",")}` : "";
  const orgParam = orgId ? `org_id=${orgId}` : "";
  
  const params = [topicParam, orgParam].filter(Boolean).join("&");
  return `${base}/ws/telemetry${params ? "?" + params : ""}`;
}

export { API };

