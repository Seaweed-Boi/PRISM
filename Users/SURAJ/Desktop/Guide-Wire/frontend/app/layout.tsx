import type { Metadata } from "next";
import "./globals.css";
import NavBar from "../components/NavBar";

export const metadata: Metadata = {
  title: "PRISM — Predictive Income Protection for Gig Workers",
  description: "AI-powered parametric insurance platform protecting gig workers from income loss caused by weather, traffic, pollution and platform outages.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NavBar />
        <main className="mx-auto max-w-7xl px-4 py-8 pt-24">{children}</main>
      </body>
    </html>
  );
}
