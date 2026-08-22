"use client";

import { motion } from "framer-motion";

interface LawSectionProps {
  onOpenChat: (prefilledText?: string) => void;
}

/** Citizen-language situations that pre-fill the chat.
 *  The chat intent classifier handles routing — citizens don't need to know
 *  whether this becomes an RTI, CPGRAMS, or Rights workflow. */
const COMMON_SITUATIONS = [
  {
    icon: "🛣️",
    label: "My road isn't repaired",
    description: "Government service complaint, civic infrastructure",
    query: "My municipal road has not been repaired for a very long time and I want to file a complaint.",
    category: "Government",
  },
  {
    icon: "📄",
    label: "I want government records",
    description: "Request information under RTI",
    query: "I want copies of government records. How do I file an RTI application?",
    category: "RTI",
  },
  {
    icon: "🏠",
    label: "Landlord won't return deposit",
    description: "Tenant rights and dispute",
    query: "My landlord is refusing to return my security deposit after I moved out.",
    category: "Tenant Rights",
  },
  {
    icon: "💼",
    label: "Employer hasn't paid salary",
    description: "Labour rights and workplace issues",
    query: "My employer has not paid my salary for the last few months.",
    category: "Labour Rights",
  },
  {
    icon: "🛒",
    label: "Defective product or service",
    description: "Consumer protection complaint",
    query: "I bought a product that is defective and the seller refuses to help me.",
    category: "Consumer Rights",
  },
  {
    icon: "🏛️",
    label: "Find government schemes",
    description: "Welfare, pension, and benefit eligibility",
    query: "I want to find out which government schemes I am eligible for.",
    category: "Schemes",
  },
] as const;

const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  Government: { bg: "rgba(167,139,250,0.1)", text: "var(--color-primary)" },
  RTI:        { bg: "rgba(129,140,248,0.1)", text: "var(--color-accent)" },
  "Tenant Rights":  { bg: "rgba(232,180,184,0.1)", text: "var(--color-secondary)" },
  "Labour Rights":  { bg: "rgba(232,180,184,0.1)", text: "var(--color-secondary)" },
  "Consumer Rights":{ bg: "rgba(167,139,250,0.1)", text: "var(--color-primary)" },
  Schemes:          { bg: "rgba(129,140,248,0.1)", text: "var(--color-accent)" },
};

export function LawSection({ onOpenChat }: LawSectionProps) {
  return (
    <section className="flex flex-col gap-5 px-4" aria-labelledby="situations-heading">
      {/* Section header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.05 }}
      >
        <h2
          id="situations-heading"
          className="text-xs font-semibold uppercase tracking-widest mb-1"
          style={{ color: "var(--color-text-faint)" }}
        >
          Common situations
        </h2>
        <p className="text-xs" style={{ color: "var(--color-text-faint)" }}>
          Select a situation to get started, or describe your own in the chat.
        </p>
      </motion.div>

      {/* Situation cards — 2 columns on mobile, 3 on desktop */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3" role="list">
        {COMMON_SITUATIONS.map((sit, i) => {
          const catColor = CATEGORY_COLORS[sit.category] ?? CATEGORY_COLORS["Government"];
          return (
            <motion.div
              key={sit.label}
              role="listitem"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.08 + i * 0.06 }}
            >
              <button
                onClick={() => onOpenChat(sit.query)}
                className="w-full h-full flex flex-col items-start gap-2.5 p-3.5 rounded-2xl text-left
                           transition-all hover:scale-[1.02] active:scale-[0.98]
                           focus-visible:outline-none focus-visible:ring-2"
                style={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  minHeight: "100px",
                }}
                aria-label={`Start: ${sit.label} — ${sit.description}`}
              >
                <span className="text-2xl" aria-hidden="true">{sit.icon}</span>
                <div className="flex-1">
                  <p className="text-sm font-semibold leading-snug" style={{ color: "var(--color-text)" }}>
                    {sit.label}
                  </p>
                  <p className="text-[10px] mt-0.5 leading-relaxed" style={{ color: "var(--color-text-faint)" }}>
                    {sit.description}
                  </p>
                </div>
                <span
                  className="text-[9px] font-semibold px-2 py-0.5 rounded-full"
                  style={{ background: catColor.bg, color: catColor.text }}
                >
                  {sit.category}
                </span>
              </button>
            </motion.div>
          );
        })}
      </div>

      {/* Not listed? → chat entry */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.5 }}
      >
        <button
          onClick={() => onOpenChat()}
          className="w-full flex flex-col items-center gap-2 py-4 px-6 rounded-2xl transition-all
                     hover:scale-[1.01] active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2"
          style={{
            background: "linear-gradient(135deg, rgba(167, 139, 250, 0.12), rgba(129, 140, 248, 0.06))",
            border: "1px solid var(--color-primary)",
          }}
          aria-label="Describe your own situation to get personalised guidance"
        >
          <span className="text-2xl" aria-hidden="true">💬</span>
          <div className="text-center">
            <p className="text-sm font-bold" style={{ color: "var(--color-primary)" }}>
              My situation is different
            </p>
            <p className="text-xs max-w-xs" style={{ color: "var(--color-text-muted)" }}>
              Describe what happened — we&apos;ll identify the right path
            </p>
          </div>
        </button>
      </motion.div>

      {/* Emergency orientation — always visible */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.35, delay: 0.6 }}
      >
        <div
          className="rounded-2xl p-3.5 text-xs leading-relaxed"
          style={{
            background: "rgba(239,68,68,0.08)",
            color: "var(--color-text-muted)",
            border: "1px solid rgba(239,68,68,0.2)",
          }}
          role="note"
          aria-label="Emergency contacts information"
        >
          <span className="font-semibold" style={{ color: "#ef4444" }}>Immediate danger?</span>
          {" "}Call{" "}
          <a href="tel:112" className="font-bold underline" style={{ color: "#ef4444" }}>112</a>
          {" "}(National Emergency) or{" "}
          <a href="tel:100" className="font-bold underline" style={{ color: "#ef4444" }}>100</a>
          {" "}(Police). Free legal aid: NALSA{" "}
          <a href="tel:15100" className="font-bold underline" style={{ color: "#ef4444" }}>15100</a>.
        </div>
      </motion.div>
    </section>
  );
}
