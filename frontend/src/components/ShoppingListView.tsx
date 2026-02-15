"use client";

import { ShoppingItem } from "@/lib/api";

interface Props {
  items: ShoppingItem[];
  onRemove?: (item: string) => void;
}

export default function ShoppingListView({ items, onRemove }: Props) {
  if (items.length === 0) {
    return (
      <div className="glass-card" style={{ padding: "2rem", textAlign: "center" }}>
        <p style={{ color: "var(--text)", fontSize: "1rem", margin: 0 }}>Shopping list is empty.</p>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "0.5rem" }}>
          Add items via Poke: &quot;Add milk to the shopping list&quot;
        </p>
      </div>
    );
  }

  return (
    <div className="entries-list">
      <div className="entry-category">
        <div className="category-header">Shopping list</div>
        <div>
          {items.map((item, j) => (
            <div key={j} className="entry-item">
              <div className="entry-key">
                {item.quantity}x {item.name}
              </div>
              <p className="entry-value">Added by {item.added_by}</p>
              {onRemove && (
                <button
                  type="button"
                  className="btn"
                  style={{ marginTop: "0.5rem", fontSize: "0.8rem", padding: "0.35rem 0.75rem" }}
                  onClick={() => onRemove(item.name)}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
