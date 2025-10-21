import type { Metadata } from "next";
import { Unbounded, Space_Grotesk, Inter } from "next/font/google";
import "./globals.css";

const unbounded = Unbounded({
  variable: "--font-unbounded",
  subsets: ["latin"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sim-U-Fi - Predictive MEV Protection",
  description: "See all possible futures of your trade before it executes. Protect against MEV with AI-powered parallel execution simulation.",
  keywords: ["DeFi", "MEV Protection", "Trading", "Ethereum", "Base", "AI", "Simulation"],
  authors: [{ name: "Sim-U-Fi Team" }],
  openGraph: {
    title: "Sim-U-Fi - Predictive MEV Protection",
    description: "See all possible futures of your trade before it executes",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${unbounded.variable} ${spaceGrotesk.variable} ${inter.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
