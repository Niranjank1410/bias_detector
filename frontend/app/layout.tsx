import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bias Detector — News Analysis",
  description: "Detect framing bias across news sources using ML",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg-primary text-text-primary">
        {/* Nav */}
        <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur border-b border-bg-border">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <span className="w-6 h-6 rounded bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center text-xs font-bold">
                B
              </span>
              <span className="font-semibold text-text-primary">Bias Detector</span>
            </a>
            <div className="flex items-center gap-6 text-sm text-text-secondary">
              <a href="/" className="hover:text-text-primary">Stories</a>
              <a href="/sources" className="hover:text-text-primary">Sources</a>
            </div>
          </div>
        </nav>

        <main className="max-w-6xl mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}