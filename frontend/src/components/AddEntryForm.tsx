"use client";

import { useState } from "react";
import { KnowledgeEntry } from "@/lib/data";

interface Props {
  onAdd: (entry: KnowledgeEntry) => void;
}

export default function AddEntryForm({ onAdd }: Props) {
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [category, setCategory] = useState("brand");
  const [toast, setToast] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim() || !value.trim()) return;

    const entry: KnowledgeEntry = {
      key: key.trim(),
      value: value.trim(),
      category,
      created_at: new Date().toISOString(),
    };

    onAdd(entry);
    setKey("");
    setValue("");
    setCategory("brand");
    setToast(true);
    setTimeout(() => setToast(false), 3000);
  }

  return (
    <>
      <form className="add-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="entry-key">Key</label>
          <input
            type="text"
            className="form-input"
            id="entry-key"
            placeholder="e.g. brand_colors"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="entry-value">Value</label>
          <input
            type="text"
            className="form-input"
            id="entry-value"
            placeholder="e.g. #FF6B35 and #004E89"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="entry-category">Category</label>
          <select
            className="form-select"
            id="entry-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="brand">Brand</option>
            <option value="policy">Policy</option>
            <option value="preference">Preference</option>
            <option value="fact">Fact</option>
          </select>
        </div>
        <button type="submit" className="btn btn-primary">Add entry</button>
      </form>
      {toast && (
        <div className="toast">
          Entry added. Switch to Entries tab to view.
        </div>
      )}
    </>
  );
}
