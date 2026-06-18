import type { Metadata } from 'next'
import '../styles/globals.css'
import GoogleAnalytics from './components/GoogleAnalytics'

export const metadata: Metadata = {
  title: 'Prijslijst Validator',
  description: 'Interactive pricelist validation tool for 100% spec completion',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="nl">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0F4C81" />
        <GoogleAnalytics />
      </head>
      <body className="bg-bg-page text-text-color">
        <div className="min-h-screen flex flex-col">
          {children}
        </div>
      </body>
    </html>
  )
}
