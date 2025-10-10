'use client';

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <title>MCP-Based API Documentation Aggregator</title>
        <meta name="description" content="AI-powered API documentation search and aggregation platform" />
      </head>
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
