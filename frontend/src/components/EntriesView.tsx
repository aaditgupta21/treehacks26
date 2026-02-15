"use client";

import { KnowledgeEntry, getEntriesByCategory, formatEntryDate } from "@/lib/data";

interface Props {
  entries: KnowledgeEntry[];
}

export default function EntriesView({ entries }: Props) {
  const groups = getEntriesByCategory(entries);

  if (groups.length === 0) {
    return <p style={{ color: "var(--text-muted)" }}>No entries yet.</p>;
  }

  return (
    <div className="entries-list">
      {groups.map((g, i) => (
        <div
          key={g.category}
          className="entry-category"
          style={{ animationDelay: `${0.15 + i * 0.05}s` }}
        >
          <div className="category-header">{g.category}</div>
          <div>
            {g.entries.map((e, j) => (
              <div key={j} className="entry-item">
                <div className="entry-key">{e.key}</div>
                <p className="entry-value">{e.value}</p>
                {e.created_at && (
                  <div className="entry-date">
                    {formatEntryDate(e.created_at)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
