"use client";

import { useState, useRef, useEffect, useCallback, useId } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { smartQuery, type SmartResponse } from "@/services/api";
import { useApp } from "@/context/AppContext";
import { Logo } from "@/components/Logo";
import { ChatHandoffTransition } from "@/components/ChatHandoffTransition";
import {
  civicJourneyForResponse,
  createCivicWorkflowLaunch,
  resolveAutomaticCivicHandoff,
  type CivicJourney,
  type CivicWorkflowLaunch,
} from "@/lib/civicWorkflowHandoff";

// ── Civic-first quick chips ────────────────────────────────────────────────────

const QUICK_CHIPS = [
  { label: "Road not repaired",     text: "My municipal road has not been repaired for a long time." },
  { label: "Government records",    text: "I want copies of government records under RTI." },
  { label: "Landlord deposit",      text: "My landlord won't return my security deposit." },
  { label: "Unpaid salary",         text: "My employer hasn't paid my salary for months." },
  { label: "Consumer complaint",    text: "I have a consumer complaint about a defective product." },
  { label: "Find schemes",          text: "I want to find government schemes I may be eligible for." },
  { label: "I need help",           text: "I'm not sure what my problem is called. Can you help me?" },
];

// Low-confidence civic suggestions — no crime categories
const LOW_CONFIDENCE_CHIPS = [
  { label: "I want government records",    text: "I want copies of government records under RTI." },
  { label: "My complaint was ignored",     text: "I filed a complaint but nothing happened. I want to escalate." },
  { label: "Landlord issue",               text: "My landlord is causing a problem and refusing to help." },
  { label: "My employer isn't paying",     text: "My employer hasn't paid my salary or provident fund." },
  { label: "Find schemes for me",          text: "I am looking for government welfare schemes I can apply for." },
];

const LANG_LABELS: Record<string, string> = {
  "hi-IN": "हिन्दी",
  "ta-IN": "தமிழ்",
  "te-IN": "తెలుగు",
  "kn-IN": "ಕನ್ನಡ",
  "ml-IN": "മലയാളം",
  "bn-IN": "বাংলা",
  "gu-IN": "ગુજરાતી",
  "pa-IN": "ਪੰਜਾਬੀ",
  "od-IN": "ଓଡ଼ିଆ",
  "mr-IN": "मराठी",
};

function parseHelplineNumber(h: string): string | null {
  const m = h.match(/\d{3,5}/);
  return m ? m[0] : null;
}

interface ChatMessage {
  role: "user" | "ai";
  text: string;
  smartData?: SmartResponse;
  requestNarrative?: string;
  isError?: boolean;
}

interface ChatModalProps {
  open: boolean;
  /** Optional pre-filled text to seed the first message */
  initialText?: string;
  onClose: () => void;
  onOpenCivic?: (launch: CivicWorkflowLaunch) => void;
}

const CIVIC_JOURNEY_LABELS: Record<CivicJourney, string> = {
  rti: "RTI Assistant",
  cpgrams: "CPGRAMS Assistant",
  schemes: "Scheme Eligibility",
  rights: "Rights Navigator",
};

const SEVERITY: Record<string, { bg: string; text: string; label: string }> = {
  critical: { bg: "rgba(239,68,68,0.2)",  text: "#ef4444", label: "URGENT" },
  high:     { bg: "rgba(249,115,22,0.2)", text: "#f97316", label: "HIGH" },
  medium:   { bg: "rgba(232,180,184,0.2)", text: "#e8b4b8", label: "MODERATE" },
  low:      { bg: "rgba(167,139,250,0.2)", text: "#a78bfa", label: "LOW" },
};

function needsCategoryPicker(data: SmartResponse | undefined): boolean {
  return Boolean(
    data && !civicJourneyForResponse(data) && (data.scenario === "unknown" || !data.guidance)
  );
}

// ── Low-confidence picker (civic-first) ─────────────────────────────────────

function LowConfidencePicker({
  onSelect,
  disabled,
}: {
  onSelect: (text: string) => void;
  disabled?: boolean;
}) {
  return (
    <div
      className="rounded-2xl p-4 flex flex-col gap-3 text-sm"
      style={{ background: "rgba(0,0,0,0.2)", border: "1px solid var(--color-border)" }}
      role="group"
      aria-label="Clarify your situation"
    >
      <p style={{ color: "var(--color-text-muted)" }}>
        Let me understand better. What&apos;s happening?
      </p>
      <div className="flex flex-wrap gap-2">
        {LOW_CONFIDENCE_CHIPS.map((chip) => (
          <button
            key={chip.label}
            onClick={() => onSelect(chip.text)}
            disabled={disabled}
            className="px-3 py-1.5 rounded-full text-xs font-medium transition-colors disabled:opacity-40"
            style={{
              background: "var(--color-primary-dim)",
              color: "var(--color-primary)",
              border: "1px solid rgba(167,139,250,0.3)",
            }}
            aria-label={`Select: ${chip.label}`}
          >
            {chip.label}
          </button>
        ))}
      </div>
      <p className="text-[10px]" style={{ color: "var(--color-text-faint)" }}>
        Or describe your situation in the box below in your own words.
      </p>
    </div>
  );
}

// ── Structured response card ────────────────────────────────────────────────

function ResponseCard({
  data,
  narrative,
  language,
  onOpenCivic,
}: {
  data: SmartResponse;
  narrative: string;
  language: string;
  onOpenCivic?: (launch: CivicWorkflowLaunch) => void;
}) {
  const [showDraft, setShowDraft] = useState(false);
  const sev = SEVERITY[data.severity] || SEVERITY.medium;
  const manualLaunch = createCivicWorkflowLaunch(data, narrative, language);

  return (
    <div
      className="rounded-2xl p-3.5 flex flex-col gap-3 text-xs"
      style={{ background: "rgba(0,0,0,0.22)", border: "1px solid var(--color-border)" }}
    >
      {/* Title + severity */}
      <div className="flex items-start justify-between gap-2">
        <span className="font-semibold text-sm leading-snug" style={{ color: "var(--color-primary)" }}>
          {data.title}
        </span>
        <span
          className="shrink-0 px-2 py-0.5 rounded-full text-[9px] font-bold tracking-wider uppercase mt-0.5"
          style={{ background: sev.bg, color: sev.text }}
          aria-label={`Severity: ${sev.label}`}
        >
          {sev.label}
        </span>
      </div>

      {/* Guidance */}
      {data.guidance && (
        <div className="whitespace-pre-line leading-relaxed" style={{ color: "var(--color-text)" }}>
          {data.guidance}
        </div>
      )}

      {/* Applicable legal sections */}
      {data.sections.length > 0 && (
        <div className="flex flex-col gap-1">
          <span
            className="font-semibold uppercase tracking-wider text-[9px]"
            style={{ color: "var(--color-secondary)" }}
          >
            Applicable sections
          </span>
          <div className="flex flex-wrap gap-1" role="list">
            {data.sections.map((s, i) => (
              <span
                key={i}
                role="listitem"
                className="px-2 py-0.5 rounded-full text-[10px]"
                style={{
                  background: "var(--color-secondary-dim)",
                  color: "var(--color-secondary)",
                  border: "1px solid rgba(232,180,184,0.2)",
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Likely outcome */}
      {data.outcome && (
        <div
          className="rounded-xl px-3 py-2"
          style={{ background: "var(--color-primary-dim)", border: "1px solid rgba(167,139,250,0.15)" }}
        >
          <span className="font-semibold" style={{ color: "var(--color-primary)" }}>Likely next step: </span>
          <span style={{ color: "var(--color-text)" }}>{data.outcome}</span>
        </div>
      )}

      {/* Civic workflow CTA */}
      {manualLaunch && onOpenCivic && (
        <button
          type="button"
          onClick={() => onOpenCivic(manualLaunch)}
          className="w-full rounded-xl px-3 py-2.5 text-sm font-semibold transition-all
                     hover:scale-[1.01] active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2"
          style={{
            background: "var(--color-primary-dim)",
            color: "var(--color-primary)",
            border: "1px solid var(--color-primary)",
          }}
          aria-label={`Continue to ${CIVIC_JOURNEY_LABELS[manualLaunch.journey]}`}
        >
          Continue to {CIVIC_JOURNEY_LABELS[manualLaunch.journey]} →
        </button>
      )}

      {/* Draft (collapsible) */}
      {data.complaint_draft && (
        <div>
          <button
            onClick={() => setShowDraft((p) => !p)}
            aria-expanded={showDraft}
            className="text-[10px] font-semibold px-2.5 py-1 rounded-full"
            style={{
              background: "var(--color-accent-dim)",
              color: "var(--color-accent)",
              border: "1px solid rgba(129,140,248,0.2)",
            }}
          >
            {showDraft ? "Hide draft ▲" : "View draft document ▼"}
          </button>
          <AnimatePresence>
            {showDraft && (
              <motion.pre
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="mt-2 whitespace-pre-wrap text-[11px] leading-relaxed rounded-xl p-2.5 overflow-hidden"
                style={{ background: "rgba(0,0,0,0.28)", color: "var(--color-text)", border: "1px solid var(--color-border)" }}
              >
                {data.complaint_draft}
              </motion.pre>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Emergency helplines */}
      {(data.severity === "critical" || data.severity === "high") && data.helplines.length > 0 && (() => {
        const num = parseHelplineNumber(data.helplines[0]);
        return num ? (
          <a
            href={`tel:${num}`}
            className="flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold tracking-wide"
            style={{
              background: "rgba(239,68,68,0.2)",
              color: "#ef4444",
              border: "2px solid rgba(239,68,68,0.45)",
              animation: "sos-pulse 2s ease-in-out infinite",
            }}
            aria-label={`Emergency: Call ${data.helplines[0]}`}
          >
            <span aria-hidden>📞</span> Call {data.helplines[0]}
          </a>
        ) : null;
      })()}

      {/* All helplines */}
      {data.helplines.length > 0 && (
        <div className="flex flex-wrap gap-1.5" role="list" aria-label="Helplines">
          {data.helplines.map((h, i) => {
            const num = parseHelplineNumber(h);
            return num ? (
              <a
                key={i}
                href={`tel:${num}`}
                role="listitem"
                className="px-2 py-0.5 rounded-full text-[10px] font-bold inline-flex items-center gap-1"
                style={{ background: "rgba(239,68,68,0.12)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.2)" }}
                aria-label={`Call helpline ${h}`}
              >
                📞 {h}
              </a>
            ) : (
              <span
                key={i}
                role="listitem"
                className="px-2 py-0.5 rounded-full text-[10px] font-bold"
                style={{ background: "rgba(239,68,68,0.12)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.2)" }}
              >
                {h}
              </span>
            );
          })}
        </div>
      )}

      {/* Language + source (lightweight trust) */}
      <div className="flex items-center justify-between text-[9px]" style={{ color: "var(--color-text-faint)" }}>
        {data.response_language && data.response_language !== "en-IN" ? (
          <span>
            Responded in {LANG_LABELS[data.response_language] || data.response_language}
          </span>
        ) : <span />}
        <span className="uppercase tracking-widest">
          {data.source === "classifier" ? "Official classification" : "AI-assisted guidance"}
        </span>
      </div>
    </div>
  );
}

// ── Error message bubble ─────────────────────────────────────────────────────

function ErrorBubble({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      className="rounded-2xl rounded-bl-sm px-4 py-3 flex flex-col gap-2 text-sm max-w-[90%] self-start"
      style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}
      role="alert"
    >
      <p style={{ color: "#ef4444" }}>We can&apos;t reach the service right now.</p>
      <button
        onClick={onRetry}
        className="text-xs font-semibold px-3 py-1.5 rounded-full self-start"
        style={{ background: "rgba(239,68,68,0.15)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.3)" }}
      >
        Try again
      </button>
    </div>
  );
}

// ── Main ChatModal ───────────────────────────────────────────────────────────

export function ChatModal({ open, initialText, onClose, onOpenCivic }: ChatModalProps) {
  const { state } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState(initialText ?? "");
  const [isLoading, setIsLoading] = useState(false);
  const [lastUserText, setLastUserText] = useState("");
  const [pendingHandoff, setPendingHandoff] = useState<CivicWorkflowLaunch | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const statusId = useId();

  // Scroll to bottom on new message
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input when modal opens
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [open]);

  // Pre-fill text from props when modal opens
  useEffect(() => {
    if (open && initialText) {
      setInput(initialText);
    }
  }, [open, initialText]);

  // Focus trap — Escape closes modal
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        // If handoff pending, cancel it
        if (pendingHandoff) {
          setPendingHandoff(null);
          return;
        }
        onClose();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose, pendingHandoff]);

  const doSend = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      setLastUserText(trimmed);
      setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
      setInput("");
      setIsLoading(true);

      try {
        const res = await smartQuery(trimmed, state.language.code);

        setMessages((prev) => [
          ...prev,
          { role: "ai", text: "", smartData: res, requestNarrative: trimmed },
        ]);

        // Check for automatic civic handoff
        const automaticLaunch = resolveAutomaticCivicHandoff(res, trimmed, state.language.code);
        if (automaticLaunch && onOpenCivic) {
          // Show transition message first, then navigate
          setPendingHandoff(automaticLaunch);
        }
      } catch (err) {
        console.error("Chat query error:", err);
        setMessages((prev) => [...prev, { role: "ai", text: "", isError: true }]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, state.language.code, onOpenCivic]
  );

  const handleRetry = useCallback(() => {
    if (lastUserText) doSend(lastUserText);
  }, [lastUserText, doSend]);

  const handleHandoffComplete = useCallback(() => {
    if (pendingHandoff && onOpenCivic) {
      onOpenCivic(pendingHandoff);
      setPendingHandoff(null);
    }
  }, [pendingHandoff, onOpenCivic]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-[55]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(2px)" }}
            aria-hidden="true"
          />

          {/* Panel */}
          <motion.div
            ref={panelRef}
            id="chat-modal"
            role="dialog"
            aria-modal="true"
            aria-label="LAWTRIX Chat Assistant"
            aria-describedby={statusId}
            className="fixed top-0 right-0 bottom-0 z-[60] flex flex-col w-full md:w-[480px] md:max-w-[90vw] relative overflow-hidden"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            style={{
              background: "var(--color-bg)",
              borderLeft: "1px solid var(--color-border-bright)",
              boxShadow: "-12px 0 48px rgba(0,0,0,0.35)",
            }}
          >
            {/* Intent detection handoff overlay */}
            <ChatHandoffTransition
              show={!!pendingHandoff}
              journey={pendingHandoff?.journey ?? null}
              onComplete={handleHandoffComplete}
            />

            {/* ── Header ── */}
            <div
              className="flex items-center justify-between px-5 py-4 border-b shrink-0"
              style={{ borderColor: "var(--color-border)" }}
            >
              <div className="flex items-center gap-2.5">
                <Logo size={22} />
                <div>
                  <h2 className="font-semibold text-sm leading-tight" style={{ color: "var(--color-text)" }}>
                    LAWTRIX
                  </h2>
                  <p className="text-[9px] leading-none" style={{ color: "var(--color-text-faint)" }}>
                    Civic &amp; Legal Assistant
                  </p>
                </div>
              </div>

              <button
                onClick={onClose}
                className="w-9 h-9 rounded-full flex items-center justify-center text-sm
                           transition-colors hover:bg-opacity-80 focus-visible:outline-none focus-visible:ring-2"
                style={{ color: "var(--color-text-muted)", background: "var(--color-surface)" }}
                aria-label="Close chat"
              >
                ✕
              </button>
            </div>

            {/* ── Messages ── */}
            <div
              className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3 min-h-0"
              role="log"
              aria-label="Chat messages"
              aria-live="polite"
            >
              {/* Empty state */}
              {messages.length === 0 && (
                <div className="text-center py-8 flex flex-col items-center gap-2">
                  <span className="text-4xl" aria-hidden>💬</span>
                  <p
                    id={statusId}
                    className="text-base font-semibold"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    Tell us what happened
                  </p>
                  <p className="text-xs max-w-[240px]" style={{ color: "var(--color-text-faint)" }}>
                    Describe your situation in plain language. We&apos;ll find the right path.
                  </p>
                </div>
              )}

              {/* Message list */}
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  className={`max-w-[92%] ${m.role === "user" ? "self-end" : "self-start"}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {m.role === "user" ? (
                    <div
                      className="rounded-2xl rounded-br-sm px-4 py-2.5 text-sm leading-relaxed"
                      style={{ background: "var(--color-accent-dim)", color: "var(--color-accent)" }}
                    >
                      {m.text}
                    </div>
                  ) : m.isError ? (
                    <ErrorBubble onRetry={handleRetry} />
                  ) : needsCategoryPicker(m.smartData) ? (
                    <LowConfidencePicker onSelect={doSend} disabled={isLoading} />
                  ) : m.smartData ? (
                    <ResponseCard
                      data={m.smartData}
                      narrative={m.requestNarrative ?? ""}
                      language={state.language.code}
                      onOpenCivic={onOpenCivic}
                    />
                  ) : (
                    <div
                      className="rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm whitespace-pre-line border-l-2 leading-relaxed"
                      style={{
                        background: "var(--color-surface)",
                        borderColor: "var(--color-primary)",
                        color: "var(--color-text)",
                      }}
                    >
                      {m.text}
                    </div>
                  )}
                </motion.div>
              ))}

              {/* Loading dots */}
              {isLoading && (
                <div
                  className="self-start flex items-center gap-2 px-4 py-3"
                  role="status"
                  aria-label="Finding the right path..."
                >
                  {[0, 1, 2].map((i) => (
                    <motion.span
                      key={i}
                      className="w-2 h-2 rounded-full"
                      style={{ background: "var(--color-primary)" }}
                      animate={{ y: [0, -5, 0] }}
                      transition={{ repeat: Infinity, duration: 0.7, delay: i * 0.15 }}
                    />
                  ))}
                  <span className="text-xs ml-1" style={{ color: "var(--color-text-faint)" }}>
                    Finding the right path…
                  </span>
                </div>
              )}

              <div ref={endRef} aria-hidden />
            </div>

            {/* ── Quick chips ── */}
            {messages.length === 0 && (
              <div
                className="px-4 pb-2 shrink-0 overflow-x-auto"
                style={{ scrollbarWidth: "none" }}
                role="group"
                aria-label="Quick situation starters"
              >
                <div className="flex gap-2 pb-1">
                  {QUICK_CHIPS.map((c) => (
                    <button
                      key={c.label}
                      onClick={() => doSend(c.text)}
                      disabled={isLoading}
                      className="chip shrink-0 disabled:opacity-40"
                      aria-label={`Start with: ${c.label}`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ── Input area ── */}
            <div
              className="flex items-end gap-2 px-4 py-3 border-t shrink-0"
              style={{ borderColor: "var(--color-border)" }}
            >
              <label htmlFor="chat-input" className="sr-only">
                Describe your situation
              </label>
              <input
                ref={inputRef}
                id="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    doSend(input);
                  }
                }}
                placeholder="Describe your situation…"
                disabled={isLoading}
                autoComplete="off"
                className="flex-1 bg-transparent text-sm outline-none disabled:opacity-50 leading-relaxed"
                style={{
                  color: "var(--color-text)",
                  minHeight: "44px",
                  paddingTop: "10px",
                  paddingBottom: "10px",
                }}
                aria-label="Describe your situation"
                aria-describedby={messages.length === 0 ? statusId : undefined}
              />
              <button
                onClick={() => doSend(input)}
                disabled={!input.trim() || isLoading}
                className="px-4 py-2.5 rounded-full text-xs font-semibold transition-all
                           disabled:opacity-40 disabled:cursor-not-allowed
                           hover:scale-[1.03] active:scale-[0.97]
                           focus-visible:outline-none focus-visible:ring-2"
                style={{
                  background: "var(--color-primary-dim)",
                  color: "var(--color-primary)",
                  border: "1px solid var(--color-primary)",
                  minHeight: "44px",
                  minWidth: "64px",
                }}
                aria-label="Send message"
              >
                Send
              </button>
            </div>

            {/* Disclaimer */}
            <p
              className="text-[9px] text-center px-4 pb-3 shrink-0"
              style={{ color: "var(--color-text-faint)" }}
            >
              Not legal advice. Consult a qualified lawyer for your specific situation.
            </p>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
