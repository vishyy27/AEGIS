import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "AEGIS | AI Deployment Risk Platform",
  description: "Predict deployment risk before production releases.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#020617] text-white overflow-hidden">
        <div className="flex">
          <Sidebar />
          <div className="flex-1 ml-[240px] h-screen overflow-y-auto">
            <Header />
            <main className="mt-16 p-8 min-h-screen">
              <div className="max-w-[1600px] mx-auto space-y-8">{children}</div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
