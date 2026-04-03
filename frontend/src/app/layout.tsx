import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PERT Estimation Tool",
  description: "PERT Estimation SDLC Tool for project planning and estimation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
