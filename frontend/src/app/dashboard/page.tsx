"use client";

import { useState, useCallback, useEffect } from "react";
import {
  getMeetings,
  getKnowledge,
  getShoppingList,
  addKnowledge as apiAddKnowledge,
  removeShoppingItem as apiRemoveShoppingItem,
  type Meeting,
  type KnowledgeEntry,
  type ShoppingItem,
} from "@/lib/api";
import CalendarView from "@/components/CalendarView";
import EntriesView from "@/components/EntriesView";
import ShoppingListView from "@/components/ShoppingListView";
import AddEntryForm from "@/components/AddEntryForm";

type Tab = "calendar" | "entries" | "shopping" | "add";

const TABS: { id: Tab; label: string }[] = [
  { id: "calendar", label: "Calendar" },
  { id: "entries", label: "Knowledge" },
  { id: "shopping", label: "Shopping" },
  { id: "add", label: "Add Entry" },
];

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("calendar");
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [shoppingList, setShoppingList] = useState<ShoppingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const teamId = "default";

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, e, s] = await Promise.all([
        getMeetings(teamId),
        getKnowledge(teamId),
        getShoppingList(teamId),
      ]);
      setMeetings(Array.isArray(m) ? m : []);
      setEntries(Array.isArray(e) ? e : []);
      setShoppingList(Array.isArray(s) ? s : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
      setMeetings([]);
      setEntries([]);
      setShoppingList([]);
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = useCallback(
    async (entry: KnowledgeEntry) => {
      try {
        await apiAddKnowledge(teamId, entry.key, entry.value, entry.category);
        setEntries((prev) => [...prev, entry]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add entry");
      }
    },
    [teamId]
  );

  const handleRemoveShopping = useCallback(
    async (item: string) => {
      try {
        await apiRemoveShoppingItem(teamId, item);
        setShoppingList((prev) => prev.filter((i) => i.name !== item));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to remove item");
      }
    },
    [teamId]
  );

  if (loading) {
    return (
      <div className="glass-card" style={{ textAlign: "center", padding: "2rem" }}>
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--peach-dark)", marginBottom: "0.5rem", fontWeight: 600 }}>
          Could not load data
        </p>
        <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
          {error}
        </p>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
          Start the API server: <code style={{ background: "rgba(0,0,0,0.1)", padding: "0.2em 0.4em", borderRadius: 4 }}>python run_api.py</code>
        </p>
        <button className="btn btn-primary" onClick={fetchData} style={{ marginTop: "1rem" }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="dash-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`dash-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "calendar" && <CalendarView meetings={meetings} />}
      {activeTab === "entries" && <EntriesView entries={entries} />}
      {activeTab === "shopping" && <ShoppingListView items={shoppingList} onRemove={handleRemoveShopping} />}
      {activeTab === "add" && <AddEntryForm onAdd={handleAdd} />}
    </>
  );
}
