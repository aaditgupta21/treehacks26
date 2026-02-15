"use client";

import { Meeting, getMeetingsByDay, formatDayHeader, formatTimeRange } from "@/lib/data";

interface Props {
  meetings: Meeting[];
}

export default function CalendarView({ meetings }: Props) {
  const byDay = getMeetingsByDay(meetings);
  const days = Object.keys(byDay).sort();

  if (days.length === 0) {
    return <p style={{ color: "var(--text-muted)" }}>No events yet.</p>;
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
