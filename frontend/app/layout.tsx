import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AFM Morphology Analysis",
  description: "CNN, U-Net, Voronoi, and ColorWheel analysis for AFM images.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
