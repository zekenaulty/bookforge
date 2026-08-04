import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "kotoba-no-kaijiba — a private living-fiction library",
  description: "Create fictional authors, begin living stories, and read or listen as each new section is written.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><body>{children}</body></html>;
}
