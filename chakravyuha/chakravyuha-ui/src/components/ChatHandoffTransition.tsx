"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { CivicJourney } from "@/lib/civicWorkflowHandoff";

const JOURNEY_MESSAGES: Record<CivicJourney, { headline: string; sub: string; icon: string }> = {
  rti: {
    icon: "📄",
    headline: "This looks like a request for government records.",
    sub: "Let\u2019s prepare your RTI application.",
  },
  cpgrams: {
    icon: "📮",
    headline: "This looks like a government service issue.",
    sub: "Let\u2019s prepare your CPGRAMS grievance.",
  },
  schemes: {
    icon: "🏛️",
    headline: "This looks like a scheme eligibility question.",
    sub: "Let\u2019s check which schemes you qualify for.",
  },
  rights: {
    icon: "🧭",
    headline: "This looks like a rights guidance situation.",
    sub: "Let\u2019s find the right information for you.",
  },
};

interface ChatHandoffTransitionProps {
  /** Whether the transition overlay is visible */
  show: boolean;
  journey: CivicJourney | null;
  /** Called after the transition auto-completes (~1.6s) */
  onComplete: () => void;
}

/**
 * Briefly shows a human-readable intent detection result
 * before the chat modal closes and the civic workflow opens.
 *
 * Duration ≈ 1.6 s — enough to be readable but not disruptive.
 */
export function ChatHandoffTransition({ show, journey, onComplete }: ChatHandoffTransitionProps) {
  useEffect(() => {
    if (!show || !journey) return;
    const timer = setTimeout(onComplete, 1600);
    return () => clearTimeout(timer);
  }, [show, journey, onComplete]);

  const msg = journey ? JOURNEY_MESSAGES[journey] : null;

  return (
    <AnimatePresence>
      {show && msg && (
        <motion.div
          className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 rounded-2xl px-6 text-center"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          style={{ background: "var(--color-bg)", backdropFilter: "blur(8px)" }}
          role="status"
          aria-live="polite"
          aria-label={`${msg.headline} ${msg.sub}`}
        >
          <motion.span
            className="text-5xl"
            initial={{ scale: 0.7 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 18, delay: 0.05 }}
            aria-hidden="true"
          >
            {msg.icon}
          </motion.span>

          <div className="flex flex-col gap-1.5">
            <p className="text-base font-semibold" style={{ color: "var(--color-text)" }}>
              {msg.headline}
            </p>
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              {msg.sub}
            </p>
          </div>

          {/* Animated progress bar */}
          <motion.div
            className="h-0.5 rounded-full"
            style={{ width: "120px", background: "var(--color-border)" }}
          >
            <motion.div
              className="h-full rounded-full"
              style={{ background: "var(--color-primary)" }}
              initial={{ width: "0%" }}
              animate={{ width: "100%" }}
              transition={{ duration: 1.5, ease: "easeInOut" }}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
