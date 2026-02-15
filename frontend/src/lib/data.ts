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
}

export interface DummyData {
  meetings: Meeting[];
  knowledge: KnowledgeEntry[];
  shoppingList: ShoppingItem[];
}

export const DUMMY_DATA: DummyData = {
  meetings: [
    {
      title: "Sprint Planning",
      start: "2025-02-17T09:00:00",
      end: "2025-02-17T10:00:00",
      attendees: ["Armaan", "Priya", "Jake"],
    },
    {
      title: "Design Review",
      start: "2025-02-17T14:00:00",
      end: "2025-02-17T15:00:00",
      attendees: ["Armaan", "Mei"],
    },
    {
      title: "Standup",
      start: "2025-02-18T09:30:00",
      end: "2025-02-18T09:45:00",
      attendees: ["Armaan", "Priya", "Jake", "Mei"],
    },
    {
      title: "Investor Prep",
      start: "2025-02-18T11:00:00",
      end: "2025-02-18T12:00:00",
      attendees: ["Armaan", "Jake"],
    },
    {
      title: "Hack Night",
      start: "2025-02-19T18:00:00",
      end: "2025-02-19T22:00:00",
      attendees: ["Armaan", "Priya", "Jake", "Mei"],
    },
    {
      title: "1:1 with Priya",
      start: "2025-02-19T10:00:00",
      end: "2025-02-19T10:30:00",
      attendees: ["Armaan", "Priya"],
    },
    {
      title: "Demo Day Rehearsal",
      start: "2025-02-20T15:00:00",
      end: "2025-02-20T16:30:00",
      attendees: ["Armaan", "Priya", "Jake", "Mei"],
    },
  ],
  knowledge: [
    { key: "brand_colors", value: "#FF6B35 and #004E89", category: "brand", created_at: "2025-02-10T09:00:00" },
    { key: "logo_font", value: "Adamina — serif, warm, approachable", category: "brand", created_at: "2025-02-10T09:05:00" },
    { key: "tagline", value: "AI that works as one with your team", category: "brand", created_at: "2025-02-11T14:30:00" },
    { key: "remote_policy", value: "Fully remote, async-first with 2 sync days (Tue & Thu)", category: "policy", created_at: "2025-02-08T10:00:00" },
    { key: "expense_limit", value: "$200/month discretionary, anything above needs approval", category: "policy", created_at: "2025-02-08T10:15:00" },
    { key: "standup_time", value: "9:30 AM PST daily", category: "preference", created_at: "2025-02-09T08:00:00" },
    { key: "deploy_day", value: "Thursdays — no deploys on Fridays", category: "preference", created_at: "2025-02-09T08:10:00" },
    { key: "coffee_order", value: "Armaan: oat latte, Priya: cold brew, Jake: drip, Mei: matcha", category: "preference", created_at: "2025-02-12T07:00:00" },
    { key: "founding_date", value: "January 15, 2025", category: "fact", created_at: "2025-02-07T12:00:00" },
    { key: "team_size", value: "4 co-founders", category: "fact", created_at: "2025-02-07T12:05:00" },
    { key: "hq_location", value: "San Francisco, CA (virtual HQ)", category: "fact", created_at: "2025-02-07T12:10:00" },
  ],
  shoppingList: [
    { name: "Sticky notes", quantity: 3, added_by: "Priya" },
    { name: "Whiteboard markers", quantity: 1, added_by: "Jake" },
    { name: "Coffee beans (Ethiopian)", quantity: 2, added_by: "Armaan" },
    { name: "HDMI adapters", quantity: 2, added_by: "Mei" },
    { name: "Blue light glasses", quantity: 4, added_by: "Priya" },
  ],
};

// Helper: group meetings by day
export function getMeetingsByDay(meetings: Meeting[]) {
  const sorted = [...meetings].sort(
    (a, b) => new Date(a.start).getTime() - new Date(b.start).getTime()
  );
  const byDay: Record<string, Meeting[]> = {};
  for (const m of sorted) {
    const key = m.start.slice(0, 10);
    if (!byDay[key]) byDay[key] = [];
    byDay[key].push(m);
  }
  return byDay;
}

// Helper: group entries by category
export function getEntriesByCategory(entries: KnowledgeEntry[]) {
  const sorted = [...entries].sort(
    (a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  );
  const byCategory: Record<string, KnowledgeEntry[]> = {};
  for (const e of sorted) {
    if (!byCategory[e.category]) byCategory[e.category] = [];
    byCategory[e.category].push(e);
  }
  const order = ["brand", "policy", "preference", "fact"];
  return order.filter((c) => byCategory[c]).map((c) => ({ category: c, entries: byCategory[c] }));
}

// Format helpers
export function formatDayHeader(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

export function formatTimeRange(start: string, end: string) {
  const s = new Date(start);
  const e = new Date(end);
  return (
    s.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" }) +
    " – " +
    e.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
  );
}

export function formatEntryDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
