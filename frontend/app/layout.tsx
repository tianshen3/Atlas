import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ATLAS — Enterprise Knowledge Assistant",
  description: "Enterprise Hybrid Retrieval-Augmented Generation (RAG) platform. Grounded technical document intelligence with dense vector search, BM25 sparse retrieval, and cross-encoder reranking.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-[#0B0E0D] text-[#E4E8E4] technical-grid-bg selection:bg-[#6F9B82]/20 selection:text-[#E4E8E4]">
        {/* WCAG Skip to Main Content link */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#151A17] focus:text-[#E4E8E4] focus:border focus:border-[#6F9B82] focus:rounded text-xs font-mono"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
