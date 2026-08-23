"use client"

import { useState, useEffect } from 'react'
import { X, Download } from 'lucide-react'
import { useInstallPrompt } from '@/hooks/useInstallPrompt'
import { Button } from '@/components/ui/button'

/**
 * Install Banner for PWA
 *
 * Shows a dismissible banner prompting users to install the app.
 * Only appears when the PWA can be installed and hasn't been dismissed.
 */
export function InstallBanner() {
  const { canInstall, install } = useInstallPrompt()
  const [dismissed, setDismissed] = useState(false)

  // Check if user has previously dismissed the banner
  useEffect(() => {
    const isDismissed = localStorage.getItem('lawtrix_install_dismissed')
    if (isDismissed === 'true') {
      setDismissed(true)
    }
  }, [])

  const handleInstall = async () => {
    const outcome = await install()
    if (outcome === 'accepted') {
      // User accepted the install prompt
      setDismissed(true)
    }
  }

  const handleDismiss = () => {
    setDismissed(true)
    localStorage.setItem('lawtrix_install_dismissed', 'true')
  }

  if (!canInstall || dismissed) {
    return null
  }

  return (
    <div className="fixed bottom-20 left-4 right-4 z-40 md:bottom-4 md:left-auto md:right-4 md:max-w-sm">
      <div className="glass rounded-lg p-4 shadow-lg border border-primary/20">
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-primary/10 p-2">
            <Download className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-sm mb-1">Install LAWTRIX</h3>
            <p className="text-xs text-muted-foreground mb-3">
              Add to your home screen for quick access and offline support
            </p>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleInstall} className="flex-1">
                Install
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDismiss}
                className="px-2"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
