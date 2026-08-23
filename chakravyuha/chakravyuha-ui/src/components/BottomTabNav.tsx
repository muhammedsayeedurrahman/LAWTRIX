"use client";

interface BottomTabNavProps {
  onTabChange: (tab: string) => void;
  activeTab: string;
  caseCount?: number;
}

const TABS = [
  { id: "home",  icon: "🏠",  label: "Home",  ariaLabel: "Go to home view" },
  { id: "civic", icon: "📁",  label: "Cases", ariaLabel: "View your cases and actions" },
  { id: "help",  icon: "❓",  label: "Help",  ariaLabel: "Emergency and legal helplines" },
];

export function BottomTabNav({ onTabChange, activeTab, caseCount = 0 }: BottomTabNavProps) {
  return (
    <div className="fixed bottom-3 left-0 right-0 z-50 flex justify-center px-4 pointer-events-none">
      <nav
        className="pointer-events-auto flex items-center gap-1.5 p-1.5 rounded-full transition-all"
        style={{
          background: "var(--color-nav-bg)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          border: "1px solid var(--color-border-bright)",
          boxShadow: "var(--color-card-shadow)",
        }}
        role="navigation"
        aria-label="Main navigation"
        suppressHydrationWarning
      >
        {TABS.map((tab) => {
          const isActive =
            activeTab === tab.id ||
            (tab.id === "civic" && ["civic", "draft", "file"].includes(activeTab));
          const showBadge = tab.id === "civic" && caseCount > 0;

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold transition-all focus:outline-none focus-visible:ring-2 ${
                isActive ? "shadow-md" : "hover:bg-white/5 opacity-80 hover:opacity-100"
              }`}
              style={{
                background: isActive ? "var(--color-primary-dim)" : "transparent",
                color: isActive ? "var(--color-primary)" : "var(--color-text-muted)",
                border: isActive ? "1px solid rgba(167, 139, 250, 0.3)" : "1px solid transparent",
                minHeight: "36px",
              }}
              aria-label={tab.ariaLabel}
              aria-current={isActive ? "page" : undefined}
              suppressHydrationWarning
            >
              <span className="relative text-sm" aria-hidden="true">
                {tab.icon}
                {showBadge && (
                  <span
                    className="absolute -top-1 -right-2 min-w-[14px] h-[14px] rounded-full flex items-center justify-center text-[9px] font-bold leading-none"
                    style={{ background: "var(--color-primary)", color: "var(--color-bg)" }}
                    aria-label={`${caseCount} active cases`}
                  >
                    {caseCount > 9 ? "9+" : caseCount}
                  </span>
                )}
              </span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
