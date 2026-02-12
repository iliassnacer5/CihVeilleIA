import React from "react"
import type { Metadata, Viewport } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'

import './globals.css'
import { LayoutContent } from './layout-content'
import { Toaster } from '@/components/ui/toaster'
import { RealTimeNotifications } from '@/components/RealTimeNotifications'

const _geist = Geist({ subsets: ['latin'] })
const _geistMono = Geist_Mono({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CIH Bank | AI Intelligence & Web Monitoring Platform',
  description: 'Enterprise banking intelligence platform for automated web intelligence, regulatory monitoring, and AI-powered document analysis',
  generator: 'v0.app',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

import { AuthProvider } from './context/AuthContext'

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <AuthProvider>
          <LayoutContent>{children}</LayoutContent>
          <RealTimeNotifications />
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  )
}
