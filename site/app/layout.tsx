import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bookshelf — Book quotes inside Codex and Claude Code",
  description:
    "Turn the pauses between Codex and Claude Code turns into a small literary reset with one compact, locally selected book quote.",
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
    title: "Bookshelf — Let the terminal widen your world",
    description:
      "A quiet book quote inside your Codex or Claude Code session, every few completed turns.",
    type: "website",
    images: [
      "https://raw.githubusercontent.com/Amal-David/bookshelf/main/site/public/og-preview.png",
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Bookshelf — Let the terminal widen your world",
    description:
      "A quiet book quote inside your Codex or Claude Code session, every few completed turns.",
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
