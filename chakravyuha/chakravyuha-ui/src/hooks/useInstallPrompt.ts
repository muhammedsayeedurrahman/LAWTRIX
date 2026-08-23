"use client"

import { useState, useEffect } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

/**
 * Hook to handle PWA install prompt
 *
 * Returns:
 * - canInstall: boolean indicating if install prompt is available
 * - install: function to trigger the install prompt
 * - isInstalled: boolean indicating if app is already installed
 */
export function useInstallPrompt() {
  const [installPromptEvent, setInstallPromptEvent] = useState<BeforeInstallPromptEvent | null>(null)
  const [isInstalled, setIsInstalled] = useState(false)

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true)
      return
    }

    // Listen for the beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: Event) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault()
      // Save the event for later use
      setInstallPromptEvent(e as BeforeInstallPromptEvent)
    }

    // Listen for app installed event
    const handleAppInstalled = () => {
      setIsInstalled(true)
      setInstallPromptEvent(null)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const install = async (): Promise<'accepted' | 'dismissed' | 'unavailable'> => {
    if (!installPromptEvent) {
      return 'unavailable'
    }

    // Show the install prompt
    await installPromptEvent.prompt()

    // Wait for the user to respond
    const { outcome } = await installPromptEvent.userChoice

    // Clear the saved prompt
    setInstallPromptEvent(null)

    return outcome
  }

  return {
    canInstall: !!installPromptEvent && !isInstalled,
    isInstalled,
    install,
  }
}
