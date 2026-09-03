import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NIRIKSHAK-AI Dashboard",
  description: "Trendy, energetic MPLADS monitoring platform",
};

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
          <header className="sticky top-0 z-50 w-full border-b bg-surface/80 backdrop-blur">
            <div className="container mx-auto flex h-16 items-center px-4 md:px-8">
              <div className="font-headline font-bold text-2xl text-primary tracking-tight">
                NIRIKSHAK<span className="text-secondary">AI</span>
              </div>
              <nav className="ml-8 hidden gap-6 md:flex font-body font-semibold">
                <a href="#" className="text-primary border-b-2 border-primary py-5">Dashboard</a>
                <a href="#" className="text-gray-600 hover:text-primary py-5 transition-colors">Projects</a>
                <a href="#" className="text-gray-600 hover:text-primary py-5 transition-colors">Analytics</a>
                <a href="#" className="text-gray-600 hover:text-primary py-5 transition-colors">MPs</a>
              </nav>
            </div>
          </header>
          <main className="container mx-auto px-4 md:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
