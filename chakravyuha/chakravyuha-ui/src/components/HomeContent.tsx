"use client";

import { useState, useCallback, useRef } from "react";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { BottomTabNav } from "@/components/BottomTabNav";
import { ChatModal } from "@/components/ChatModal";
import { ComplaintDraftCard } from "@/components/ComplaintDraftCard";
import { OpenClawCard } from "@/components/OpenClawCard";
import { CivicAssistant, type CivicFilingHandoff, type CivicJourney } from "@/components/CivicAssistant";
import type { CivicWorkflowLaunch } from "@/lib/civicWorkflowHandoff";
import { Preloader } from "@/components/Preloader";
import { CurtainTransition } from "@/components/CurtainTransition";
import { useApp } from "@/context/AppContext";

export default function HomeContent() {
  const { state } = useApp();
  const [activeTab, setActiveTab] = useState("home");
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInitialText, setChatInitialText] = useState<string | undefined>(undefined);
  const [chatAutoSend, setChatAutoSend] = useState<boolean>(false);
  const [loaded, setLoaded] = useState(false);
  const [showCurtain, setShowCurtain] = useState(false);
  const [civicJourney, setCivicJourney] = useState<CivicJourney>("rti");
  const [civicContext, setCivicContext] = useState<CivicWorkflowLaunch | null>(null);
  const [civicLaunchVersion, setCivicLaunchVersion] = useState(0);
  const [filingHandoff, setFilingHandoff] = useState<{ portalId: string; userData: Record<string, string> } | null>(null);
  const prevTabRef = useRef("home");

  const switchTab = useCallback((tab: string) => {
    if (tab === prevTabRef.current) return;

    if (tab !== "chat") {
      setShowCurtain(true);
      setTimeout(() => {
        setActiveTab(tab);
        prevTabRef.current = tab;
        setShowCurtain(false);
      }, 350);
    } else {
      setActiveTab(tab);
      prevTabRef.current = tab;
    }
  }, []);

  /** Open the chat assistant with optional pre-filled text and auto-send */
  const handleStartChat = useCallback(
    (prefilledText?: string, options?: { autoSend?: boolean }) => {
      setChatInitialText(prefilledText ?? "");
      setChatAutoSend(options?.autoSend ?? false);
      setChatOpen(true);
    },
    []
  );

  /** Called when chat intent detection resolves to a civic workflow */
  const handleChatCivicHandoff = useCallback((launch: CivicWorkflowLaunch) => {
    setChatOpen(false);
    setChatInitialText(undefined);
    setChatAutoSend(false);
    setCivicJourney(launch.journey);
    setCivicContext(launch);
    setCivicLaunchVersion((v) => v + 1);
    switchTab("civic");
  }, [switchTab]);

  const handleCloseChat = useCallback(() => {
    setChatOpen(false);
    setChatInitialText(undefined);
    setChatAutoSend(false);
  }, []);

  const handleCivicFilingHandoff = useCallback((handoff: CivicFilingHandoff) => {
    setFilingHandoff(handoff);
    switchTab("file");
  }, [switchTab]);

  const handleCivicLegalHandoff = useCallback((target: "chat" | "draft") => {
    if (target === "chat") {
      handleStartChat();
      return;
    }
    switchTab("draft");
  }, [handleStartChat, switchTab]);

  const handleTabChange = useCallback((tab: string) => {
    if (tab === "help") {
      // Smooth scroll to trust / helpline section if on home, or switch to home then scroll
      if (activeTab !== "home") {
        switchTab("home");
        setTimeout(() => {
          document.getElementById("trust-section")?.scrollIntoView({ behavior: "smooth" });
        }, 400);
      } else {
        document.getElementById("trust-section")?.scrollIntoView({ behavior: "smooth" });
      }
      return;
    }
    if (tab === "civic") {
      if (!["civic", "draft", "file"].includes(activeTab)) {
        switchTab("civic");
      }
      return;
    }
    switchTab(tab);
  }, [activeTab, switchTab]);

  // Count active cases for badge
  const caseCount = state.caseList?.length ?? 0;

  if (!loaded) {
    return <Preloader onComplete={() => setLoaded(true)} />;
  }

  const isOnCivicVariant = ["civic", "draft", "file"].includes(activeTab);

  return (
    <div
      className="min-h-screen flex flex-col pb-24 bg-grid relative selection:bg-purple-500 selection:text-white"
      style={{ backgroundColor: "var(--color-bg)" }}
    >
      {/* Curtain transition overlay */}
      <CurtainTransition show={showCurtain} />

      <Header />

      <main
        id="main-content"
        className="flex-1 max-w-3xl mx-auto w-full flex flex-col gap-8 py-4 relative z-10"
        tabIndex={-1}
      >
        {activeTab === "file" ? (
          /* ── Filing Tab (OpenClaw) ── */
          <ErrorBoundary>
            <OpenClawCard
              key={`${filingHandoff?.portalId ?? "none"}-${filingHandoff?.userData.description?.slice(0, 24) ?? "blank"}`}
              initialPortalId={filingHandoff?.portalId}
              initialUserData={filingHandoff?.userData}
            />
          </ErrorBoundary>
        ) : activeTab === "civic" ? (
          /* ── Civic Workflow Tab ── */
          <ErrorBoundary>
            <CivicAssistant
              key={`${civicJourney}-${civicLaunchVersion}`}
              initialJourney={civicJourney}
              initialContext={civicContext}
              onOpenClaw={handleCivicFilingHandoff}
              onOpenLegal={handleCivicLegalHandoff}
            />
          </ErrorBoundary>
        ) : activeTab === "draft" ? (
          /* ── Document Draft Tab ── */
          <ErrorBoundary>
            <ComplaintDraftCard />
          </ErrorBoundary>
        ) : (
          /* ── Home Tab ── */
          <>
            <HeroSection onStartChat={handleStartChat} />

            {/* ── Secondary Trust & Helplines Area ── */}
            <section
              id="trust-section"
              className="px-4 flex flex-col gap-4 mt-2"
              aria-labelledby="helplines-heading"
            >
              <div
                className="rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs"
                style={{
                  background: "var(--color-surface-elevated)",
                  border: "1px solid var(--color-border)",
                  boxShadow: "var(--color-card-shadow)",
                }}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl" aria-hidden="true">
                    🛡️
                  </span>
                  <div>
                    <h3
                      id="helplines-heading"
                      className="font-bold text-sm"
                      style={{ color: "var(--color-text)" }}
                    >
                      Emergency &amp; Official Legal Aid
                    </h3>
                    <p style={{ color: "var(--color-text-muted)" }}>
                      National toll-free citizen helplines:
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <a
                    href="tel:15100"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold transition-all hover:scale-105"
                    style={{
                      background: "rgba(167, 139, 250, 0.15)",
                      color: "var(--color-primary)",
                      border: "1px solid rgba(167, 139, 250, 0.3)",
                    }}
                    aria-label="Call NALSA Free Legal Aid 15100"
                  >
                    <span>NALSA Legal Aid:</span>
                    <span className="underline">15100</span>
                  </a>

                  <a
                    href="tel:112"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold transition-all hover:scale-105"
                    style={{
                      background: "rgba(239, 68, 68, 0.12)",
                      color: "#ef4444",
                      border: "1px solid rgba(239, 68, 68, 0.25)",
                    }}
                    aria-label="Call National Emergency 112"
                  >
                    <span>Emergency:</span>
                    <span className="underline">112</span>
                  </a>
                </div>
              </div>

              {/* Legal Disclaimer */}
              <p
                className="text-[11px] text-center px-4 leading-relaxed"
                style={{ color: "var(--color-text-faint)" }}
              >
                LAWTRIX provides structured civic pathways and legal orientation. It is not formal legal counsel. For representation in court, consult a certified advocate or your State Legal Services Authority.
              </p>
            </section>
          </>
        )}
      </main>

      {/* Sleek Floating Bottom Navigation */}
      <BottomTabNav
        activeTab={isOnCivicVariant ? "civic" : activeTab}
        onTabChange={handleTabChange}
        caseCount={caseCount}
      />

      {/* Unified Chat Assistant Modal */}
      <ChatModal
        open={chatOpen}
        initialText={chatInitialText}
        autoSend={chatAutoSend}
        onClose={handleCloseChat}
        onOpenCivic={handleChatCivicHandoff}
      />
    </div>
  );
}
