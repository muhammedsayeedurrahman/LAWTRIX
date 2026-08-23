"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { CivicJourney } from "@/lib/civicWorkflowHandoff";

const JOURNEY_MESSAGES: Record<CivicJourney, { headline: string; sub: string; icon: string }> = {
  cpgrams: {
    icon: "📮",
    headline: "Government service issue detected.",
    sub: "Let\u2019s prepare the complaint.",
  },
  rti: {
    icon: "📄",
    headline: "This looks like a government records request.",
    sub: "Let\u2019s prepare the RTI.",
  },
  schemes: {
    icon: "🏛️",
    headline: "Government scheme query detected.",
    sub: "Let\u2019s check which schemes you qualify for.",
  },
  rights: {
    icon: "🧭",
    headline: "Rights guidance pathway detected.",
    sub: "Let\u2019s prepare your practical next step.",
  },
};

interface ChatHandoffTransitionProps {
  /** Whether the transition overlay is visible */
  show: boolean;
  journey: CivicJourney | null;
  /** Called after the transition auto-completes (~1.5s) */
  onComplete: () => void;
}

/**
 * Briefly shows a human-readable intent detection result
 * before transitioning smoothly to the civic action workflow.
 */
export function ChatHandoffTransition({ show, journey, onComplete }: ChatHandoffTransitionProps) {
  useEffect(() => {
    if (!show || !journey) return;
    const timer = setTimeout(onComplete, 1500);
    return () => clearTimeout(timer);
  }, [show, journey, onComplete]);

  const msg = journey ? JOURNEY_MESSAGES[journey] : null;

  return (
    <AnimatePresence>
      {show && msg && (
        <motion.div
          className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 rounded-2xl px-6 text-center"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          style={{ background: "var(--color-modal-bg)", backdropFilter: "blur(16px)" }}
          role="status"
          aria-live="polite"
          aria-label={`${msg.headline} ${msg.sub}`}
        >
          <motion.span
            className="text-5xl"
            initial={{ scale: 0.6, y: 10 }}
            animate={{ scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 350, damping: 20 }}
            aria-hidden="true"
          >
            {msg.icon}
          </motion.span>

          <div className="flex flex-col gap-1.5 max-w-xs">
            <p className="text-base font-bold tracking-tight" style={{ color: "var(--color-text)" }}>
              {msg.headline}
            </p>
            <p className="text-sm font-medium" style={{ color: "var(--color-primary)" }}>
              {msg.sub}
            </p>
          </div>

          {/* Animated progress bar */}
          <div
            className="h-1 rounded-full overflow-hidden mt-2"
            style={{ width: "140px", background: "var(--color-surface-bright)" }}
          >
            <motion.div
              className="h-full rounded-full"
              style={{ background: "linear-gradient(90deg, var(--color-primary), var(--color-accent))" }}
              initial={{ width: "0%" }}
              animate={{ width: "100%" }}
              transition={{ duration: 1.4, ease: "easeInOut" }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
