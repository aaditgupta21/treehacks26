/**
 * API client - calls http://localhost:8001 directly. Set NEXT_PUBLIC_API_URL to override.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface Meeting {
  title: string;
  start: string;
  end: string;
  attendees: string[];
}

export interface KnowledgeEntry {
  key: string;
  value: string;
  category: string;
  created_at?: string;
}

export interface ShoppingItem {
  name: string;
  quantity: number;
  added_by: string;
  created_at?: string;
}

export interface ApiHealth {
  ok: boolean;
  elasticsearch: boolean;
}

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getHealth(): Promise<ApiHealth> {
  return fetchApi<ApiHealth>("/api/health");
}

export async function getMeetings(teamId = "default"): Promise<Meeting[]> {
  const data = await fetchApi<{ meetings: Meeting[] }>(`/api/meetings?team_id=${encodeURIComponent(teamId)}`);
  return data.meetings;
}

export async function deleteMeeting(
  teamId: string,
  title: string,
  start: string,
  end: string
): Promise<void> {
  const params = new URLSearchParams({ team_id: teamId, title });
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  await fetchApi(`/api/meetings?${params}`, { method: "DELETE" });
}

export async function getKnowledge(
  teamId = "default",
  query?: string,
  category?: string
): Promise<KnowledgeEntry[]> {
  const params = new URLSearchParams({ team_id: teamId });
  if (query) params.set("q", query);
  if (category) params.set("category", category);
  const data = await fetchApi<{ knowledge: KnowledgeEntry[] }>(`/api/knowledge?${params}`);
  return data.knowledge;
}

export async function addKnowledge(
  teamId: string,
  key: string,
  value: string,
  category: string
): Promise<void> {
  const params = new URLSearchParams({ team_id: teamId, key, value, category });
  await fetchApi(`/api/knowledge?${params}`, { method: "POST" });
}

export async function getShoppingList(
  teamId = "default",
  filterItem?: string
): Promise<ShoppingItem[]> {
  const params = new URLSearchParams({ team_id: teamId });
  if (filterItem) params.set("filter_item", filterItem);
  const data = await fetchApi<{ shoppingList: ShoppingItem[] }>(`/api/shopping?${params}`);
  return data.shoppingList;
}

export async function addShoppingItem(
  teamId: string,
  item: string,
  quantity = "1",
  addedBy = "unknown"
): Promise<void> {
  const params = new URLSearchParams({ team_id: teamId, item, quantity, added_by: addedBy });
  await fetchApi(`/api/shopping?${params}`, { method: "POST" });
}

export async function removeShoppingItem(teamId: string, item: string): Promise<void> {
  const params = new URLSearchParams({ team_id: teamId, item });
  await fetchApi(`/api/shopping?${params}`, { method: "DELETE" });
}
