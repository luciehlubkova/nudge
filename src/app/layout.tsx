import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Nudge",
  description: "Osobní task manager s rychlým braindumpem",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="cs" className={`${geistSans.variable} h-full`}>
      <body className="min-h-full bg-cream text-very-dark antialiased">
        {children}
      </body>
    </html>
  );
}
