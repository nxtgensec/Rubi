import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { VisitorCounter } from "@/components/visitor-counter";

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
  title: "Rubi Dashboard",
  description: "AI voice employee dashboard for Indian businesses.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        {children}
        <VisitorCounter />
      </body>
    </html>
  );
}
