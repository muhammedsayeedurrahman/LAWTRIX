"use client";

interface BottomTabNavProps {
  onTabChange: (tab: string) => void;
  activeTab: string;
  caseCount?: number;
}

const TABS = [
  { id: "home",  icon: "🏠",  label: "Home",   ariaLabel: "Go to home" },
  { id: "chat",  icon: "💬",  label: "Chat",   ariaLabel: "Open chat assistant" },
  { id: "civic", icon: "🧭",  label: "Cases",  ariaLabel: "View active cases and workflows" },
  { id: "help",  icon: "❓",  label: "Help",   ariaLabel: "Get help" },
];

export function BottomTabNav({ onTabChange, activeTab, caseCount = 0 }: BottomTabNavProps) {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 glass-bright flex justify-around py-2 px-2"
      role="navigation"
      aria-label="Main navigation"
      suppressHydrationWarning
    >
      {TABS.map((tab) => {
        const isActive = activeTab === tab.id || (tab.id === "civic" && ["civic", "draft", "file"].includes(activeTab));
        const showBadge = tab.id === "civic" && caseCount > 0;

        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id === "help" ? "home" : tab.id)}
            className={`bottom-nav-tab ${isActive ? "active" : ""}`}
            aria-label={tab.ariaLabel}
            aria-current={isActive ? "page" : undefined}
            suppressHydrationWarning
          >
            <span className="relative text-lg" aria-hidden="true">
              {tab.icon}
              {showBadge && (
                <span
                  className="absolute -top-1 -right-2 min-w-[14px] h-[14px] rounded-full flex items-center
                             justify-center text-[9px] font-bold leading-none"
                  style={{ background: "var(--color-primary)", color: "var(--color-bg)" }}
                  aria-label={`${caseCount} active case${caseCount !== 1 ? "s" : ""}`}
                >
                  {caseCount > 9 ? "9+" : caseCount}
                </span>
              )}
            </span>
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
