"use client";

import { motion } from "framer-motion";
import { useCallback } from "react";

/** Pre-filled situations that open ChatModal with a realistic civic query.
 *  These are shown as quick-start chips on the home page hero. */
const SITUATIONS: Array<{ label: string; icon: string; query: string }> = [
  { label: "Road complaint",       icon: "🛣️",  query: "My municipal road has not been repaired for a long time."                },
  { label: "Government records",   icon: "📄",  query: "I want copies of records showing how much was spent on road repair."      },
  { label: "Landlord issue",       icon: "🏠",  query: "My landlord won't return my security deposit after I moved out."          },
  { label: "Unpaid salary",        icon: "💼",  query: "My employer hasn't paid my salary for the last three months."            },
  { label: "Consumer complaint",   icon: "🛒",  query: "I bought a product that is defective and the seller refuses a refund."   },
  { label: "Find schemes",         icon: "🏛️",  query: "I am looking for government schemes I might be eligible for."            },
];

interface HeroSectionProps {
  onStartChat: (prefilledText?: string) => void;
}

export function HeroSection({ onStartChat }: HeroSectionProps) {
  const handleSituationClick = useCallback(
    (query: string) => {
      onStartChat(query);
    },
    [onStartChat]
  );

  return (
    <section
      className="relative flex flex-col items-center text-center gap-6 pt-10 pb-6 px-4"
      aria-labelledby="hero-heading"
    >
      {/* Brand wordmark */}
      <motion.div
        className="flex flex-col items-center gap-1"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <span
          className="text-[11px] tracking-[0.35em] font-semibold uppercase"
          style={{ color: "var(--color-secondary)" }}
        >
          India&apos;s Civic &amp; Legal Assistant
        </span>
        <h1
          id="hero-heading"
          className="text-5xl sm:text-6xl font-bold leading-none tracking-tight"
          style={{ fontFamily: "var(--font-playfair)", color: "var(--color-text)" }}
        >
          LAWTRIX
        </h1>
      </motion.div>

      {/* Primary message — citizen-first */}
      <motion.div
        className="flex flex-col gap-2"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.15 }}
      >
        <p
          className="text-xl sm:text-2xl font-semibold leading-snug"
          style={{ color: "var(--color-text)" }}
        >
          Tell us what happened.
        </p>
        <p
          className="text-sm max-w-sm leading-relaxed mx-auto"
          style={{ color: "var(--color-text-muted)" }}
        >
          We&apos;ll help you find the right government, legal, or welfare path — and prepare the next action.
        </p>
      </motion.div>

      {/* Primary CTA */}
      <motion.div
        className="flex flex-col sm:flex-row items-center gap-3"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.28 }}
      >
        <button
          id="hero-start-btn"
          onClick={() => onStartChat()}
          className="flex items-center gap-2 px-7 py-3 rounded-full text-sm font-semibold transition-all
                     hover:scale-[1.03] active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2
                     focus-visible:ring-offset-2"
          style={{
            background: "linear-gradient(135deg, rgba(167, 139, 250, 0.25), rgba(129, 140, 248, 0.12))",
            border: "1px solid var(--color-primary)",
            color: "var(--color-primary)",
            boxShadow: "0 0 24px var(--color-primary-glow)",
          }}
          aria-label="Start a conversation about your situation"
        >
          Start with your problem
          <span aria-hidden="true">→</span>
        </button>

        <button
          onClick={() => onStartChat("I would like to speak instead of type.")}
          className="flex items-center gap-1.5 px-5 py-3 rounded-full text-sm font-medium transition-all
                     hover:scale-[1.02] active:scale-[0.97]"
          style={{
            border: "1px solid var(--color-border)",
            color: "var(--color-text-muted)",
            background: "var(--color-surface)",
          }}
          aria-label="Use voice input instead"
        >
          <span aria-hidden="true">🎤</span> Speak instead
        </button>
      </motion.div>

      {/* Common Situations — pre-fill chat */}
      <motion.div
        className="w-full max-w-lg"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <p
          className="text-[10px] font-semibold uppercase tracking-widest mb-3"
          style={{ color: "var(--color-text-faint)" }}
        >
          Common situations
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {SITUATIONS.map((sit, i) => (
            <motion.button
              key={sit.label}
              onClick={() => handleSituationClick(sit.query)}
              className="chip"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.42 + i * 0.06 }}
              aria-label={`Start with: ${sit.label}`}
            >
              {sit.icon} {sit.label}
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* How it works — three concise steps */}
      <motion.div
        className="w-full max-w-lg pt-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.65 }}
      >
        <p
          className="text-[10px] font-semibold uppercase tracking-widest mb-3"
          style={{ color: "var(--color-text-faint)" }}
        >
          How it works
        </p>
        <div className="grid grid-cols-3 gap-3 sm:gap-4">
          {[
            { step: "1", label: "Tell us", desc: "Describe your situation in plain language" },
            { step: "2", label: "We identify", desc: "The right government or legal path" },
            { step: "3", label: "You confirm", desc: "Review and act on the next step" },
          ].map(({ step, label, desc }) => (
            <div key={step} className="flex flex-col items-center gap-1.5 text-center">
              <span
                className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                style={{ background: "var(--color-primary-dim)", color: "var(--color-primary)", border: "1px solid var(--color-border-bright)" }}
                aria-hidden="true"
              >
                {step}
              </span>
              <p className="text-xs font-semibold" style={{ color: "var(--color-text)" }}>{label}</p>
              <p className="text-[10px] leading-relaxed" style={{ color: "var(--color-text-faint)" }}>{desc}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
