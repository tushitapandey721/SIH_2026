import type { Metadata } from "next";
import { Bebas_Neue, Outfit, Cinzel } from "next/font/google";
import "./globals.css";

const bebasNeue = Bebas_Neue({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-bebas",
});

const cinzel = Cinzel({
  subsets: ["latin"],
  variable: "--font-cinzel",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "IP-SAKTI Sahayak | Statutory AI Assistant for Ayurvedic IP & Regulatory Affairs",
  description: "Multilingual, citation-grounded statutory AI for Traditional Knowledge & Ayurvedic IP and Regulatory Affairs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${bebasNeue.variable} ${cinzel.variable} ${outfit.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-[#050403] text-[#ede8d5] selection:bg-amber-500/30 selection:text-amber-200">
        {children}
      </body>
    </html>
  );
}
