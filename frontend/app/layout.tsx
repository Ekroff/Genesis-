import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "GENESIS — AI Business Launcher",
  description:
    "Launch your business in 30 minutes with 6 AI agents. Free for Indian MSMEs. Logo, website, payments, outreach, Google listing, and legal docs — all automated.",
  keywords: [
    "AI business launcher",
    "MSME India",
    "small business",
    "UPI payments",
    "business automation",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          {/* Background floating orbs for depth */}
          <div className="orb orb-1" aria-hidden="true" />
          <div className="orb orb-2" aria-hidden="true" />
          <div className="orb orb-3" aria-hidden="true" />

          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
