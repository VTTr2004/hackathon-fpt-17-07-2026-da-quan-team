import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Startup Lens",
  description: "Đánh giá startup và hỏi đáp tài liệu với Gemini",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>
        <header className="topbar">
          <Link href="/" className="brand">
            <span className="brandMark">SL</span>
            <span>Startup Lens</span>
          </Link>
          <span className="providerBadge">Powered by Gemini</span>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}

