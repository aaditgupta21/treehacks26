/**
 * Dummy data for Team Brain mock frontend.
 * No API calls — all data is static and local.
 */

const DUMMY_DATA = {
  team: {
    id: "default",
    name: "TreeHacks Team",
  },

  meetings: [
    { id: "m1", title: "Sprint Planning", start: "2025-02-17T10:00:00", end: "2025-02-17T11:00:00", attendees: ["Alice", "Bob", "Charlie"] },
    { id: "m2", title: "Design Review", start: "2025-02-18T14:00:00", end: "2025-02-18T15:30:00", attendees: ["Alice", "Bob"] },
    { id: "m3", title: "Demo Day Prep", start: "2025-02-19T09:00:00", end: "2025-02-19T10:00:00", attendees: ["Alice", "Bob", "Charlie", "Diana"] },
    { id: "m4", title: "Investor Call", start: "2025-02-20T16:00:00", end: "2025-02-20T17:00:00", attendees: ["Alice", "Diana"] },
    { id: "m5", title: "Retrospective", start: "2025-02-21T11:00:00", end: "2025-02-21T12:00:00", attendees: ["Alice", "Bob", "Charlie"] },
    { id: "m6", title: "Product Roadmap", start: "2025-02-17T14:00:00", end: "2025-02-17T15:00:00", attendees: ["Bob", "Charlie", "Diana"] },
  ],

  knowledge: [
    { key: "brand_colors", value: "#FF6B35 and #004E89", category: "brand", created_at: "2025-02-10T09:00:00" },
    { key: "company_name", value: "Team Brain", category: "brand", created_at: "2025-02-08T14:30:00" },
    { key: "logo_usage", value: "Use full logo on light backgrounds; icon-only for avatars", category: "brand", created_at: "2025-02-11T11:20:00" },
    { key: "pto_policy", value: "15 days PTO per year, must request 2 weeks in advance", category: "policy", created_at: "2025-02-05T10:00:00" },
    { key: "remote_work", value: "Hybrid: 2 days in office minimum", category: "policy", created_at: "2025-02-06T09:15:00" },
    { key: "expense_limit", value: "Meals under $25 no approval needed", category: "policy", created_at: "2025-02-07T16:45:00" },
    { key: "standup_time", value: "Daily at 9:30am PT", category: "preference", created_at: "2025-02-09T08:00:00" },
    { key: "coffee_preference", value: "Oatly oat milk in the kitchen", category: "preference", created_at: "2025-02-12T09:30:00" },
    { key: "meeting_default", value: "Default to 25min meetings unless specified", category: "preference", created_at: "2025-02-13T14:00:00" },
    { key: "launch_date", value: "TreeHacks 2026 — Feb 14-16", category: "fact", created_at: "2025-02-01T12:00:00" },
    { key: "team_size", value: "4 full-time, 2 contractors", category: "fact", created_at: "2025-02-03T11:00:00" },
    { key: "stack", value: "Python, FastMCP, Poke integration", category: "fact", created_at: "2025-02-04T15:30:00" },
  ],

  shoppingList: [
    { id: "s1", name: "Milk", quantity: "2", added_by: "Alice" },
    { id: "s2", name: "Bread", quantity: "1", added_by: "Bob" },
    { id: "s3", name: "Coffee beans", quantity: "1", added_by: "Charlie" },
    { id: "s4", name: "Oat milk", quantity: "2", added_by: "Alice" },
    { id: "s5", name: "Snacks for hackathon", quantity: "5", added_by: "Diana" },
  ],
};
