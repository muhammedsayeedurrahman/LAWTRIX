"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useRef, useCallback, useEffect } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { smartVoice } from "@/services/api";
import { useApp } from "@/context/AppContext";

/** Pre-filled citizen situations that start the unified assistant flow */
const COMMON_SITUATIONS: Array<{
  label: string;
  icon: string;
  query: string;
  badge: string;
}> = [
  {
    label: "Road complaint",
    icon: "🛣️",
    query: "My municipal road has not been repaired.",
    badge: "CPGRAMS",
  },
  {
    label: "Government records / RTI",
    icon: "📄",
    query: "I want copies of records showing how much was spent repairing this road.",
    badge: "RTI",
  },
  {
    label: "Landlord dispute",
    icon: "🏠",
    query: "My landlord won't return my security deposit.",
    badge: "Tenant",
  },
  {
    label: "Unpaid salary",
    icon: "💼",
    query: "My employer hasn't paid my salary.",
    badge: "Labour",
  },
  {
    label: "Consumer complaint",
    icon: "🛒",
    query: "I bought a defective product and the seller refuses a refund.",
    badge: "Consumer",
  },
  {
    label: "Find schemes",
    icon: "🏛️",
    query: "I want to find government schemes I may qualify for.",
    badge: "Schemes",
  },
];

/** 6 core capability areas citizens can understand in seconds */
const CAPABILITIES = [
  {
    id: "rti",
    icon: "📄",
    title: "RTI (Right to Information)",
    desc: "Request government records, sanctioned fund utilization, municipal files & inspection orders.",
    exampleQuery: "I want to file an RTI to inspect government expenditure records.",
  },
  {
    id: "cpgrams",
    icon: "📮",
    title: "CPGRAMS (Public Grievance)",
    desc: "Escalate delayed civic infrastructure, potholed roads, water supply & government service failures.",
    exampleQuery: "My municipal road has not been repaired for months.",
  },
  {
    id: "schemes",
    icon: "🏛️",
    title: "Government Schemes",
    desc: "Discover social welfare pensions, health coverage, student scholarships & financial aid you qualify for.",
    exampleQuery: "I want to check which government welfare schemes I am eligible for.",
  },
  {
    id: "tenant",
    icon: "🏠",
    title: "Tenant Rights",
    desc: "Resolution pathways for unreturned security deposits, unlawful eviction notices & rental disputes.",
    exampleQuery: "My landlord won't return my security deposit after I moved out.",
  },
  {
    id: "consumer",
    icon: "🛒",
    title: "Consumer Rights",
    desc: "Remedies for defective goods, denied refunds, misleading ads & deficiency in service.",
    exampleQuery: "I bought a defective product and the company refuses to replace or refund it.",
  },
  {
    id: "labour",
    icon: "💼",
    title: "Labour & Workplace",
    desc: "Guidance on withheld salaries, delayed provident funds, gratuity & unlawful termination.",
    exampleQuery: "My employer has not paid my salary for two months.",
  },
];

/** 5-step citizen intelligence flow without technical jargon */
const HOW_IT_WORKS_STEPS = [
  {
    num: "1",
    label: "Tell us",
    desc: "Describe what happened or what you need in plain words.",
  },
  {
    num: "2",
    label: "We understand",
    desc: "We analyze your issue without requiring legal jargon.",
  },
  {
    num: "3",
    label: "We find the path",
    desc: "We identify the exact government, welfare, or legal pathway.",
  },
  {
    num: "4",
    label: "We prepare the action",
    desc: "We structure the grievance, RTI request, or right next step.",
  },
  {
    num: "5",
    label: "You review & confirm",
    desc: "You check and confirm before any official action is taken.",
  },
];

interface HeroSectionProps {
  onStartChat: (prefilledText?: string, options?: { autoSend?: boolean }) => void;
}

export function HeroSection({ onStartChat }: HeroSectionProps) {
  const { state } = useApp();
  const [inputText, setInputText] = useState("");
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState<string | null>(null);

  const {
    recorderState,
    audioBlob,
    startRecording,
    stopRecording,
    clearRecording,
    error: recorderError,
  } = useAudioRecorder();

  const isRecording = recorderState === "recording";
  const inputRef = useRef<HTMLInputElement>(null);

  // Handle voice recording submission
  useEffect(() => {
    if (!audioBlob || audioBlob.size === 0) return;

    let isMounted = true;
    const processVoiceBlob = async () => {
      setIsProcessingVoice(true);
      setVoiceStatus("Transcribing voice...");
      try {
        const res = await smartVoice(audioBlob, state.language.code);
        if (!isMounted) return;

        if (res.transcript && res.transcript.trim()) {
          const transcript = res.transcript.trim();
          setInputText(transcript);
          setVoiceStatus(null);
          // Automatically launch search with transcribed text
          onStartChat(transcript, { autoSend: true });
        } else {
          setVoiceStatus("Could not hear speech clearly. Please try again or type.");
          setTimeout(() => setVoiceStatus(null), 3000);
        }
      } catch (err) {
        console.error("Hero voice processing error:", err);
        if (isMounted) {
          setVoiceStatus("Voice unavailable. You can type what happened below.");
          setTimeout(() => setVoiceStatus(null), 3000);
        }
      } finally {
        if (isMounted) {
          setIsProcessingVoice(false);
          clearRecording();
        }
      }
    };

    processVoiceBlob();

    return () => {
      isMounted = false;
    };
  }, [audioBlob, state.language.code, onStartChat, clearRecording]);

  const handleVoiceToggle = useCallback(async () => {
    if (isRecording) {
      stopRecording();
    } else {
      setVoiceStatus(null);
      await startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const handleSubmit = useCallback(
    (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      const trimmed = inputText.trim();
      if (!trimmed) {
        inputRef.current?.focus();
        return;
      }
      onStartChat(trimmed, { autoSend: true });
      setInputText("");
    },
    [inputText, onStartChat]
  );

  const handleSituationClick = useCallback(
    (query: string) => {
      onStartChat(query, { autoSend: true });
    },
    [onStartChat]
  );

  return (
    <section
      className="relative flex flex-col items-center text-center gap-7 pt-4 pb-8 px-4 w-full"
      aria-labelledby="hero-heading"
    >
      {/* ── Brand Wordmark & Tagline ── */}
      <motion.div
        className="flex flex-col items-center gap-1.5"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      >
        <span
          className="text-[10px] tracking-[0.3em] font-bold uppercase px-3 py-1 rounded-full border"
          style={{
            color: "var(--color-primary)",
            borderColor: "rgba(167, 139, 250, 0.25)",
            background: "var(--color-primary-dim)",
          }}
        >
          India&apos;s Civic &amp; Legal Action Assistant
        </span>

        <h1
          id="hero-heading"
          className="text-4xl sm:text-5xl md:text-6xl font-extrabold leading-none tracking-tight mt-1"
          style={{
            fontFamily: "var(--font-playfair)",
            color: "var(--color-text)",
            letterSpacing: "-0.02em",
          }}
        >
          LAWTRIX
        </h1>
      </motion.div>

      {/* ── Primary Framing ── */}
      <motion.div
        className="flex flex-col gap-2 max-w-lg mx-auto"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.1 }}
      >
        <p
          className="text-2xl sm:text-3xl font-bold leading-tight tracking-tight"
          style={{ color: "var(--color-text)" }}
        >
          Tell us what happened.
        </p>
        <p
          className="text-sm sm:text-base leading-relaxed"
          style={{ color: "var(--color-text-muted)" }}
        >
          We&apos;ll help you find the right government, legal, welfare, or civic pathway — and prepare the action.
        </p>
      </motion.div>

      {/* ── Unified Input (Type + Voice) ── */}
      <motion.div
        className="w-full max-w-2xl mx-auto"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.18 }}
      >
        <form
          onSubmit={handleSubmit}
          className="relative flex items-center gap-2 p-2 sm:p-2.5 rounded-2xl transition-all shadow-xl"
          style={{
            background: "var(--color-surface)",
            border: isRecording ? "1px solid #ef4444" : "1px solid var(--color-border-bright)",
            boxShadow: isRecording
              ? "0 0 25px rgba(239, 68, 68, 0.25)"
              : "0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px var(--color-primary-glow)",
          }}
        >
          {/* Voice Input Button */}
          <button
            type="button"
            onClick={handleVoiceToggle}
            disabled={isProcessingVoice}
            className={`relative flex items-center justify-center gap-1.5 px-3 sm:px-4 py-2.5 rounded-xl text-xs font-semibold transition-all shrink-0 ${
              isRecording ? "animate-pulse" : "hover:scale-[1.03]"
            }`}
            style={{
              background: isRecording ? "rgba(239, 68, 68, 0.2)" : "var(--color-primary-dim)",
              color: isRecording ? "#ef4444" : "var(--color-primary)",
              border: isRecording
                ? "1px solid rgba(239, 68, 68, 0.5)"
                : "1px solid rgba(167, 139, 250, 0.3)",
              minHeight: "44px",
            }}
            aria-label={isRecording ? "Stop recording" : "Speak your situation in your language"}
            title={isRecording ? "Stop recording" : "Speak in Hindi, Tamil, Telugu, English & more"}
          >
            <span className="text-base" aria-hidden="true">
              {isRecording ? "⏹️" : "🎙️"}
            </span>
            <span className="hidden sm:inline">
              {isRecording ? "Listening..." : "Speak"}
            </span>
          </button>

          {/* Text Input */}
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isRecording || isProcessingVoice}
            placeholder={
              isRecording
                ? "Listening... speak what happened or what you need..."
                : isProcessingVoice
                ? "Transcribing voice input..."
                : "Tell us what happened or what you need..."
            }
            className="flex-1 bg-transparent text-sm sm:text-base outline-none px-2 text-left disabled:opacity-60"
            style={{
              color: "var(--color-text)",
              minHeight: "44px",
            }}
            aria-label="Tell us what happened or what you need"
          />

          {/* Submit Action */}
          <button
            type="submit"
            disabled={!inputText.trim() || isRecording || isProcessingVoice}
            className="flex items-center justify-center gap-1.5 px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all shrink-0 disabled:opacity-40 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: "linear-gradient(135deg, var(--color-primary), #818cf8)",
              color: "#0a0a1a",
              boxShadow: "0 0 15px rgba(167, 139, 250, 0.3)",
              minHeight: "44px",
            }}
            aria-label="Find pathway"
          >
            <span>Send</span>
            <span aria-hidden="true">→</span>
          </button>
        </form>

        {/* Live Audio Status / Feedback */}
        <AnimatePresence>
          {(voiceStatus || recorderError) && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-2 text-xs font-medium px-3 py-1.5 rounded-lg text-left"
              style={{
                background: "rgba(167, 139, 250, 0.1)",
                color: recorderError ? "#ef4444" : "var(--color-primary)",
                border: "1px solid rgba(167, 139, 250, 0.2)",
              }}
              role="status"
            >
              {voiceStatus || recorderError}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── Section 1: Common Situations (Immediate Quick Actions) ── */}
      <motion.div
        className="w-full max-w-2xl mx-auto flex flex-col gap-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25 }}
      >
        <div className="flex items-center justify-between px-1">
          <p
            className="text-[11px] font-semibold uppercase tracking-widest"
            style={{ color: "var(--color-text-faint)" }}
          >
            Common situations
          </p>
          <span className="text-[10px]" style={{ color: "var(--color-text-faint)" }}>
            Tap to start immediately
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
          {COMMON_SITUATIONS.map((sit, i) => (
            <motion.button
              key={sit.label}
              type="button"
              onClick={() => handleSituationClick(sit.query)}
              className="flex items-center justify-between gap-2 p-3 rounded-xl text-left transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2"
              style={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
              }}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.28 + i * 0.04 }}
              aria-label={`Start situation: ${sit.label}`}
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <span className="text-lg shrink-0" aria-hidden="true">
                  {sit.icon}
                </span>
                <span
                  className="text-xs font-semibold truncate leading-tight"
                  style={{ color: "var(--color-text)" }}
                >
                  {sit.label}
                </span>
              </div>
              <span
                className="text-[9px] font-semibold px-1.5 py-0.5 rounded shrink-0 hidden sm:inline"
                style={{
                  background: "var(--color-primary-dim)",
                  color: "var(--color-primary)",
                }}
              >
                {sit.badge}
              </span>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* ── Section 2: What can LAWTRIX help with? (Clear Capabilities) ── */}
      <motion.div
        className="w-full max-w-2xl mx-auto flex flex-col gap-3 pt-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.38 }}
      >
        <div className="text-left px-1">
          <h2
            className="text-sm font-bold tracking-tight"
            style={{ color: "var(--color-text)" }}
          >
            What can LAWTRIX help with?
          </h2>
          <p className="text-xs mt-0.5" style={{ color: "var(--color-text-muted)" }}>
            You describe the issue in plain words — we connect you to the official pathway.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
          {CAPABILITIES.map((cap) => (
            <button
              key={cap.id}
              type="button"
              onClick={() => handleSituationClick(cap.exampleQuery)}
              className="p-3.5 rounded-2xl transition-all hover:scale-[1.01] active:scale-[0.99] text-left flex flex-col gap-1.5 focus-visible:outline-none focus-visible:ring-2"
              style={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
              }}
              aria-label={`Learn more about ${cap.title}`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xl" aria-hidden="true">
                  {cap.icon}
                </span>
                <h3
                  className="text-xs font-bold"
                  style={{ color: "var(--color-primary)" }}
                >
                  {cap.title}
                </h3>
              </div>
              <p
                className="text-[11px] leading-relaxed"
                style={{ color: "var(--color-text-muted)" }}
              >
                {cap.desc}
              </p>
            </button>
          ))}
        </div>
      </motion.div>

      {/* ── Section 3: How LAWTRIX Works (5-Step Citizen Intelligence Flow) ── */}
      <motion.div
        className="w-full max-w-2xl mx-auto flex flex-col gap-4 pt-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.48 }}
      >
        <div className="text-left px-1">
          <h2
            className="text-sm font-bold tracking-tight"
            style={{ color: "var(--color-text)" }}
          >
            How it works
          </h2>
          <p className="text-xs mt-0.5" style={{ color: "var(--color-text-muted)" }}>
            Clear, transparent guidance from plain words to a reviewed next action.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          {HOW_IT_WORKS_STEPS.map((step, idx) => (
            <div
              key={step.num}
              className={`flex flex-col items-center text-center p-3 rounded-xl gap-1.5 ${
                idx === 4 ? "col-span-2 sm:col-span-1" : ""
              }`}
              style={{
                background: "rgba(10, 10, 26, 0.5)",
                border: "1px solid var(--color-border)",
              }}
            >
              <span
                className="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold"
                style={{
                  background: "var(--color-primary-dim)",
                  color: "var(--color-primary)",
                  border: "1px solid rgba(167, 139, 250, 0.3)",
                }}
                aria-hidden="true"
              >
                {step.num}
              </span>
              <p
                className="text-xs font-bold leading-tight"
                style={{ color: "var(--color-text)" }}
              >
                {step.label}
              </p>
              <p
                className="text-[10px] leading-tight"
                style={{ color: "var(--color-text-faint)" }}
              >
                {step.desc}
              </p>
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
