"use client"

import { WifiOff } from 'lucide-react'
import { useOnlineStatus } from '@/hooks/useOnlineStatus'

/**
 * Offline Indicator
 *
 * Shows a persistent banner when the user is offline.
 * Disappears automatically when connectivity is restored.
 */
export function OfflineIndicator() {
  const isOnline = useOnlineStatus()

  if (isOnline) {
    return null
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-destructive text-destructive-foreground">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-center gap-2 text-sm">
          <WifiOff className="h-4 w-4" />
          <span>You are offline. Changes will be saved and synced when you reconnect.</span>
        </div>
      </div>
    </div>
  )
}
