"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useApp } from "@/context/AppContext";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";

export function Header() {
  const { state, setLanguage, supportedLanguages } = useApp();
  const [langOpen, setLangOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setLangOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setLangOpen(false);
      triggerRef.current?.focus();
    }
  };

  return (
    <>
      {/* Skip-to-main link for keyboard users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:rounded-lg focus:px-4 focus:py-2 focus:text-sm focus:font-semibold"
        style={{ background: "var(--color-primary)", color: "var(--color-bg)" }}
      >
        Skip to main content
      </a>

      <header
        className="sticky top-0 z-50 flex items-center justify-between px-4 sm:px-6 py-3.5"
        role="banner"
        style={{
          background: "rgba(10, 10, 26, 0.88)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div className="relative shrink-0">
            <div
              className="absolute inset-[-2px] rounded-full opacity-50"
              style={{
                background: "conic-gradient(from 0deg, #a78bfa, #e8b4b8, #818cf8, #a78bfa)",
                animation: "spin 10s linear infinite",
              }}
              aria-hidden="true"
            />
            <div
              className="relative rounded-full flex items-center justify-center"
              style={{ background: "var(--color-bg-2)" }}
            >
              <Logo size={36} />
            </div>
          </div>

          <div>
            <div
              className="text-base font-bold leading-tight tracking-tight"
              style={{ color: "var(--color-text)", fontFamily: "var(--font-playfair)" }}
              aria-label="LAWTRIX — Civic and Legal Assistant"
            >
              LAWTRIX
            </div>
            <p
              className="text-[9px] leading-none tracking-wider uppercase"
              style={{ color: "var(--color-text-faint)" }}
              aria-hidden="true"
            >
              Civic &amp; Legal Help
            </p>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle />

          {/* Language Picker */}
          <div ref={dropdownRef} className="relative" onKeyDown={handleKeyDown}>
            <button
              ref={triggerRef}
              id="lang-picker-trigger"
              onClick={() => setLangOpen((v) => !v)}
              aria-haspopup="listbox"
              aria-expanded={langOpen}
              aria-controls="lang-picker-list"
              aria-label={`Language: ${state.language.label}. Click to change.`}
              className="flex items-center gap-1.5 text-xs rounded-full px-3 py-1.5 transition-all focus:outline-none focus-visible:ring-2"
              style={{
                border: "1px solid var(--color-border)",
                color: "var(--color-text-muted)",
                background: "var(--color-surface)",
              }}
            >
              <span style={{ color: "var(--color-text)" }}>{state.language.label}</span>
              <span style={{ color: "var(--color-text-faint)" }} aria-hidden="true">
                {langOpen ? "▲" : "▼"}
              </span>
            </button>

            <AnimatePresence>
              {langOpen && (
                <motion.ul
                  id="lang-picker-list"
                  role="listbox"
                  aria-label="Select language"
                  aria-labelledby="lang-picker-trigger"
                  initial={{ opacity: 0, y: -8, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.96 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-10 rounded-xl shadow-2xl py-1.5 min-w-[160px] z-50"
                  style={{ background: "var(--color-bg-2)", border: "1px solid var(--color-border-bright)" }}
                >
                  {supportedLanguages.map((lang) => (
                    <li
                      key={lang.code}
                      role="option"
                      aria-selected={state.language.code === lang.code}
                      tabIndex={0}
                      className="px-4 py-2.5 text-sm cursor-pointer transition-colors focus:outline-none focus-visible:bg-opacity-50"
                      style={{
                        color: state.language.code === lang.code ? "var(--color-primary)" : "var(--color-text-muted)",
                        background: state.language.code === lang.code ? "var(--color-primary-dim)" : "transparent",
                        minHeight: "44px",
                        display: "flex",
                        alignItems: "center",
                      }}
                      onClick={() => {
                        setLanguage(lang);
                        setLangOpen(false);
                        triggerRef.current?.focus();
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setLanguage(lang);
                          setLangOpen(false);
                          triggerRef.current?.focus();
                        }
                      }}
                    >
                      {lang.label}
                    </li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>

          {/* Backend status — subtle dot only, no internal labels exposed */}
          <span
            className="hidden sm:block w-2 h-2 rounded-full shrink-0"
            style={{
              background: state.backendOnline ? "#22c55e" : "#f59e0b",
              boxShadow: state.backendOnline ? "0 0 6px #22c55e88" : "0 0 6px #f59e0b88",
            }}
            role="status"
            aria-label={state.backendOnline ? "Service available" : "Service temporarily unavailable"}
            title={state.backendOnline ? "Service available" : "Service temporarily unavailable"}
          />
        </div>
      </header>
    </>
  );
}
