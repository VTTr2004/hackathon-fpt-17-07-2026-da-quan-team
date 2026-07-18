import type { Metadata } from "next";
import "./globals.css";
import AppChrome from "./AppChrome";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Startup Lens",
  description: "Đánh giá startup và hỏi đáp tài liệu với Gemini",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <AppChrome>{children}</AppChrome>
        </AuthProvider>
      </body>
    </html>
  );
}

