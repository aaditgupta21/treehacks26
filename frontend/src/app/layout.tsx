import type { Metadata } from "next";
import "./globals.css";
import FluidCanvas from "@/components/FluidCanvas";

export const metadata: Metadata = {
  title: "Rally",
  description: "AI that works as one with your team",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>
        <FluidCanvas />
        <div className="app-shell">{children}</div>
      </body>
    </html>
  );
}
