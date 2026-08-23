"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

export type ThemeId = "dark" | "light" | "emerald" | "terracotta";

export interface ThemeOption {
  id: ThemeId;
  name: string;
  category: "dark" | "light";
  icon: string;
  badge: string;
  colors: [string, string, string]; // [bg, primary, accent/secondary]
}

export const THEMES: ThemeOption[] = [
  {
    id: "dark",
    name: "Judicial Amethyst",
    category: "dark",
    icon: "🌙",
    badge: "Dark",
    colors: ["#090918", "#a78bfa", "#e8b4b8"],
  },
  {
    id: "light",
    name: "Royal Parchment",
    category: "light",
    icon: "🏛️",
    badge: "Rich Light",
    colors: ["#fcfaf6", "#4338ca", "#b45309"],
  },
  {
    id: "emerald",
    name: "Sovereign Emerald",
    category: "dark",
    icon: "⚖️",
    badge: "Deep Forest",
    colors: ["#041410", "#10b981", "#fbbf24"],
  },
  {
    id: "terracotta",
    name: "Silk Saffron",
    category: "light",
    icon: "🌅",
    badge: "Warm Light",
    colors: ["#fdfbf7", "#c2410c", "#0f766e"],
  },
];

export function ThemeToggle() {
  const [currentTheme, setCurrentTheme] = useState<ThemeId>("dark");
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Initialize from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("chakra-theme") as ThemeId | null;
    if (saved && THEMES.some((t) => t.id === saved)) {
      setCurrentTheme(saved);
      document.documentElement.setAttribute("data-theme", saved);
    }
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const selectTheme = useCallback(
    (themeId: ThemeId, e?: React.MouseEvent) => {
      const applyTheme = () => {
        document.documentElement.setAttribute("data-theme", themeId);
        setCurrentTheme(themeId);
        localStorage.setItem("chakra-theme", themeId);
        setIsOpen(false);
      };

      const supportsViewTransitions =
        typeof document !== "undefined" && "startViewTransition" in document;

      if (supportsViewTransitions && e) {
        const x = e.clientX;
        const y = e.clientY;
        const endRadius = Math.hypot(
          Math.max(x, window.innerWidth - x),
          Math.max(y, window.innerHeight - y)
        );

        const transition = (
          document as unknown as {
            startViewTransition: (cb: () => void) => { ready: Promise<void> };
          }
        ).startViewTransition(applyTheme);

        transition.ready.then(() => {
          document.documentElement.animate(
            {
              clipPath: [
                `circle(0px at ${x}px ${y}px)`,
                `circle(${endRadius}px at ${x}px ${y}px)`,
              ],
            },
            {
              duration: 400,
              easing: "cubic-bezier(0.16, 1, 0.3, 1)",
              pseudoElement: "::view-transition-new(root)",
            }
          );
        });
      } else {
        applyTheme();
      }
    },
    []
  );

  const activeThemeObj = THEMES.find((t) => t.id === currentTheme) || THEMES[0];

  return (
    <div ref={dropdownRef} className="relative">
      {/* Theme Trigger Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Theme: ${activeThemeObj.name}. Click to change theme.`}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all hover:scale-[1.02] focus:outline-none focus-visible:ring-2"
        style={{
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          color: "var(--color-text)",
          boxShadow: "var(--color-input-shadow)",
          minHeight: "36px",
        }}
      >
        <span className="text-sm" aria-hidden="true">
          {activeThemeObj.icon}
        </span>
        <span className="hidden md:inline font-medium text-[11px]" style={{ color: "var(--color-text-muted)" }}>
          {activeThemeObj.name}
        </span>
        {/* Color preview dots */}
        <span className="flex items-center gap-0.5 ml-0.5">
          <span
            className="w-2 h-2 rounded-full border border-black/10"
            style={{ background: activeThemeObj.colors[0] }}
            aria-hidden="true"
          />
          <span
            className="w-2 h-2 rounded-full"
            style={{ background: activeThemeObj.colors[1] }}
            aria-hidden="true"
          />
        </span>
      </button>

      {/* Theme Selection Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.ul
            role="listbox"
            aria-label="Select color theme"
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-11 rounded-2xl shadow-2xl p-2 min-w-[220px] z-50 flex flex-col gap-1"
            style={{
              background: "var(--color-surface-elevated)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              border: "1px solid var(--color-border-bright)",
              boxShadow: "var(--color-card-shadow)",
            }}
          >
            <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider" style={{ color: "var(--color-text-faint)" }}>
              Palette &amp; Atmosphere
            </div>

            {THEMES.map((t) => {
              const isSelected = currentTheme === t.id;
              return (
                <li
                  key={t.id}
                  role="option"
                  aria-selected={isSelected}
                  tabIndex={0}
                  className="flex items-center justify-between gap-3 px-3 py-2 rounded-xl text-xs cursor-pointer transition-all focus:outline-none"
                  style={{
                    background: isSelected ? "var(--color-primary-dim)" : "transparent",
                    border: isSelected ? "1px solid var(--color-border-bright)" : "1px solid transparent",
                    color: isSelected ? "var(--color-primary)" : "var(--color-text)",
                  }}
                  onClick={(e) => selectTheme(t.id, e)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      selectTheme(t.id);
                    }
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base" aria-hidden="true">
                      {t.icon}
                    </span>
                    <div className="flex flex-col">
                      <span className="font-bold text-xs leading-tight">
                        {t.name}
                      </span>
                      <span className="text-[9px]" style={{ color: "var(--color-text-faint)" }}>
                        {t.badge}
                      </span>
                    </div>
                  </div>

                  {/* Swatch dots */}
                  <div className="flex items-center gap-1 shrink-0">
                    <span
                      className="w-3 h-3 rounded-full border border-black/10 shadow-sm"
                      style={{ background: t.colors[0] }}
                      title="Background"
                    />
                    <span
                      className="w-3 h-3 rounded-full shadow-sm"
                      style={{ background: t.colors[1] }}
                      title="Primary"
                    />
                    <span
                      className="w-3 h-3 rounded-full shadow-sm"
                      style={{ background: t.colors[2] }}
                      title="Accent"
                    />
                  </div>
                </li>
              );
            })}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
