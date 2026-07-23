import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Operyx AI",
  description: "Call-to-trade PoC dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <nav className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-6xl mx-auto flex items-center gap-8">
            <span className="text-xl font-bold text-indigo-600">Operyx AI</span>
            <Link href="/calls" className="text-gray-600 hover:text-indigo-600">
              Calls
            </Link>
            <Link href="/reviews" className="text-gray-600 hover:text-indigo-600">
              Reviews
            </Link>
            <Link href="/evaluations" className="text-gray-600 hover:text-indigo-600">
              Evaluations
            </Link>
            <Link href="/prompts" className="text-gray-600 hover:text-indigo-600">
              Prompts
            </Link>
            <Link href="/analytics" className="text-gray-600 hover:text-indigo-600">
              Analytics
            </Link>
            <Link href="/export" className="text-gray-600 hover:text-indigo-600">
              Export
            </Link>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
