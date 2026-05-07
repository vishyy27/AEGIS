import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import AICommandBar from "@/components/AICommandBar";
import { WebSocketProvider } from "@/providers/WebSocketProvider";

export const metadata: Metadata = {
  title: "AEGIS — Deployment Intelligence",
  description: "AI-native deployment risk prediction and operational intelligence platform.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body className="overflow-hidden">
        <WebSocketProvider>
          <div className="flex">
            <Sidebar />
            <div className="flex-1 ml-[220px] h-screen overflow-y-auto">
              <Header />
              <main className="mt-14 px-6 py-6">
                <div className="max-w-[1400px] mx-auto">{children}</div>
              </main>
            </div>
          </div>
          <AICommandBar />
        </WebSocketProvider>
      </body>
    </html>
  );
}
