import type { Metadata } from "next";
import { AppNavigation } from "@/components/AppNavigation";
import { ReviewsProvider } from "@/components/ReviewsProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Movie Agent",
  description: "Catalog-grounded, personalized movie recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <AppNavigation />
        <ReviewsProvider>{children}</ReviewsProvider>
      </body>
    </html>
  );
}
