import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Roadview | BlackRoad',
  description: 'Live journey streaming on an interactive map',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-black text-white">{children}</body>
    </html>
  )
}
