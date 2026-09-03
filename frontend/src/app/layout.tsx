import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NIRIKSHAK-AI Dashboard",
  description: "Trendy, energetic MPLADS monitoring platform",
};

import Navbar from "@/components/Navbar";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700&family=Poppins:wght@400;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" />
      </head>
      <body className="font-body antialiased">
        <div className="min-h-screen bg-background">
          <Navbar />
          <main className="container mx-auto px-4 md:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
