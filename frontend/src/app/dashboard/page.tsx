"use client";

import { useState, useCallback } from "react";
import { DUMMY_DATA, KnowledgeEntry } from "@/lib/data";
import CalendarView from "@/components/CalendarView";
import EntriesView from "@/components/EntriesView";
import AddEntryForm from "@/components/AddEntryForm";

type Tab = "calendar" | "entries" | "add";

const TABS: { id: Tab; label: string }[] = [
  { id: "calendar", label: "Calendar" },
  { id: "entries", label: "Entries" },
  { id: "add", label: "Add Entry" },
];

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("calendar");
  const [addedEntries, setAddedEntries] = useState<KnowledgeEntry[]>([]);

  const allEntries = [...DUMMY_DATA.knowledge, ...addedEntries];

  const handleAdd = useCallback((entry: KnowledgeEntry) => {
    setAddedEntries((prev) => [...prev, entry]);
  }, []);

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

      {activeTab === "calendar" && (
        <CalendarView meetings={DUMMY_DATA.meetings} />
      )}
      {activeTab === "entries" && (
        <EntriesView entries={allEntries} />
      )}
      {activeTab === "add" && (
        <AddEntryForm onAdd={handleAdd} />
      )}
    </>
  );
}
