"use client";

import { Meeting, getMeetingsByDay, formatDayHeader, formatTimeRange } from "@/lib/data";

interface Props {
  meetings: Meeting[];
}

export default function CalendarView({ meetings = [] }: Props) {
  const safeMeetings = Array.isArray(meetings) ? meetings : [];
  const byDay = getMeetingsByDay(safeMeetings);
  const days = Object.keys(byDay).sort();

  if (days.length === 0) {
    return (
      <div className="glass-card" style={{ padding: "2rem", textAlign: "center" }}>
        <p style={{ color: "var(--text)", fontSize: "1rem", margin: 0 }}>No events yet.</p>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "0.5rem" }}>
          Add meetings via Poke or the Add Entry tab.
        </p>
      </div>
    );
  }

  return (
    <div className="calendar-grid">
      {days.map((day, i) => (
        <div
          key={day}
          className="glass-card"
          style={{ animationDelay: `${0.15 + i * 0.05}s` }}
        >
          <div className="day-header">
            {formatDayHeader(day + "T12:00:00")}
          </div>
          <div className="day-events">
            {byDay[day].map((m, j) => (
              <article key={j} className="calendar-event">
                <h3 className="event-title">{m.title}</h3>
                <div className="event-time">
                  {formatTimeRange(m.start, m.end)}
                </div>
                <div className="event-attendees">
                  {m.attendees.map((a) => (
                    <span key={a}>{a}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
