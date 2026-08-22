import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { AppProvider } from "@/context/AppContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

export const metadata: Metadata = {
  title: "LAWTRIX — Civic & Legal Assistant for India",
  description:
    "Tell us what happened. LAWTRIX helps Indian citizens find the right government, legal, or welfare path — RTI, CPGRAMS, Scheme Eligibility, Rights Navigator, and more.",
  keywords: [
    "civic assistant", "legal assistant", "India", "RTI", "government schemes",
    "CPGRAMS", "consumer rights", "tenant rights", "labour rights", "multilingual",
    "LAWTRIX",
  ],
  openGraph: {
    title: "LAWTRIX — Civic & Legal Assistant for India",
    description: "Tell us what happened. We'll find the right government, legal, or welfare path.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body className={`${inter.variable} ${playfair.variable} font-sans antialiased`}>
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
