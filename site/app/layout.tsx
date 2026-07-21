import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bookshelf — Ambient book quotes for coding agents",
  description:
    "2,539 curated quotes from 983 books, available as an Agent Skill for Codex, Claude, Hermes, and Pi.",
  keywords: [
    "Agent Skills",
    "Codex",
    "Claude Code",
    "Hermes Agent",
    "Pi coding agent",
    "books",
    "quotes",
  ],
  openGraph: {
    title: "Bookshelf — Keep the books close",
    description:
      "A terminal library and ambient quote companion for AI coding agents.",
    type: "website",
    images: [
      "https://raw.githubusercontent.com/Amal-David/bookshelf/main/site/public/og-preview.png",
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Bookshelf — Keep the books close",
    description:
      "A terminal library and ambient quote companion for AI coding agents.",
    images: [
      "https://raw.githubusercontent.com/Amal-David/bookshelf/main/site/public/og-preview.png",
    ],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#f1ecd9",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
