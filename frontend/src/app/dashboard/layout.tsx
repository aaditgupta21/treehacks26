"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

function HeaderDate() {
  const [dateStr, setDateStr] = useState("");

  useEffect(() => {
    setDateStr(
      new Date().toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
      })
    );
  }, []);

  return <span className="header-date">{dateStr}</span>;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <header className="header-bar">
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <HeaderDate />
        </div>
        <Link href="/" className="logo">
          RALLY
        </Link>
        <div />
      </header>
      {children}
    </>
  );
}
