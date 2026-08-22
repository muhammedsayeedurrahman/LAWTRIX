"use client";

import { Suspense, lazy, useState, useCallback, useRef } from "react";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { LawSection } from "@/components/LawSection";
import { BottomTabNav } from "@/components/BottomTabNav";
import { ChatModal } from "@/components/ChatModal";
import { Card } from "@/components/Card";
import { ComplaintDraftCard } from "@/components/ComplaintDraftCard";
import { OpenClawCard } from "@/components/OpenClawCard";
import { CivicAssistant, type CivicFilingHandoff, type CivicJourney } from "@/components/CivicAssistant";
import type { CivicWorkflowLaunch } from "@/lib/civicWorkflowHandoff";
import { Preloader } from "@/components/Preloader";
import { CurtainTransition } from "@/components/CurtainTransition";
import { useApp } from "@/context/AppContext";

// Voice card is heavy — lazy-load it
const VoiceCard = lazy(() =>
  import("@/components/VoiceCard").then((m) => ({ default: m.VoiceCard }))
);

export default function HomeContent() {
  const { state } = useApp();
  const [activeTab, setActiveTab] = useState("home");
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInitialText, setChatInitialText] = useState<string | undefined>(undefined);
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
      }, 400);
    } else {
      setActiveTab(tab);
      prevTabRef.current = tab;
    }
  }, []);

  /** Open the chat modal, optionally with a pre-filled message */
  const handleStartChat = useCallback((prefilledText?: string) => {
    setChatInitialText(prefilledText ?? "");
    setChatOpen(true);
    setActiveTab("chat");
    prevTabRef.current = "chat";
  }, []);

  const handleOpenCivic = useCallback((journey: CivicJourney = "rti") => {
    setCivicJourney(journey);
    setCivicContext(null);
    setCivicLaunchVersion((v) => v + 1);
    switchTab("civic");
  }, [switchTab]);

  /** Called when chat intent detection resolves to a civic workflow */
  const handleChatCivicHandoff = useCallback((launch: CivicWorkflowLaunch) => {
    // The ChatHandoffTransition component inside ChatModal already showed the
    // "Got it. Preparing your grievance..." message before this fires.
    setChatOpen(false);
    setChatInitialText(undefined);
    setCivicJourney(launch.journey);
    setCivicContext(launch);
    setCivicLaunchVersion((v) => v + 1);
    switchTab("civic");
  }, [switchTab]);

  const handleCloseChat = useCallback(() => {
    setChatOpen(false);
    setChatInitialText(undefined);
    if (prevTabRef.current === "chat") {
      setActiveTab("home");
      prevTabRef.current = "home";
    }
  }, []);

  const handleOpenFile = useCallback((portal?: string) => {
    setFilingHandoff(portal ? { portalId: portal, userData: {} } : null);
    switchTab("file");
  }, [switchTab]);

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
    if (tab === "chat") {
      handleStartChat();
      return;
    }
    if (tab === "civic") {
      // If we're already on a civic workflow, just no-op or go to civic home
      if (!["civic", "draft", "file"].includes(activeTab)) {
        switchTab("civic");
      }
      return;
    }
    switchTab(tab);
  }, [activeTab, handleStartChat, switchTab]);

  // Count active cases for badge
  const caseCount = state.caseList?.length ?? 0;

  if (!loaded) {
    return <Preloader onComplete={() => setLoaded(true)} />;
  }

  const isOnCivicVariant = ["civic", "draft", "file"].includes(activeTab);

  return (
    <div
      className="min-h-screen flex flex-col pb-20 bg-grid relative"
      style={{ backgroundColor: "var(--color-bg)" }}
    >
      {/* Curtain transition overlay */}
      <CurtainTransition show={showCurtain} />

      <Header />

      <main
        id="main-content"
        className="flex-1 max-w-3xl mx-auto w-full flex flex-col gap-8 py-6 relative z-10"
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

            <LawSection onOpenChat={handleStartChat} />

            {/* Voice card — secondary feature, below the fold */}
            <ErrorBoundary>
              <div className="px-4">
                <Card>
                  <Card.Header>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl" aria-hidden>🎤</span>
                      <div>
                        <h2 className="font-bold text-sm" style={{ color: "var(--color-text)" }}>
                          Speak your situation
                        </h2>
                        <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                          Multilingual voice input in 10+ Indian languages
                        </p>
                      </div>
                    </div>
                  </Card.Header>
                  <Card.Body>
                    <Suspense
                      fallback={
                        <div
                          className="flex items-center justify-center py-10 text-sm"
                          style={{ color: "var(--color-text-faint)" }}
                        >
                          Loading voice assistant…
                        </div>
                      }
                    >
                      <VoiceCard />
                    </Suspense>
                  </Card.Body>
                </Card>
              </div>
            </ErrorBoundary>
          </>
        )}

        {/* Disclaimer — always visible */}
        <p
          className="text-xs text-center px-4"
          style={{ color: "var(--color-text-faint)" }}
        >
          Not legal advice. Consult a qualified lawyer for your specific situation.{" "}
          <span aria-hidden>·</span> NALSA free legal aid:{" "}
          <a href="tel:15100" className="underline" style={{ color: "var(--color-primary)" }}>
            15100
          </a>
        </p>
      </main>

      {/* Bottom navigation */}
      <BottomTabNav
        activeTab={isOnCivicVariant ? "civic" : activeTab}
        onTabChange={handleTabChange}
        caseCount={caseCount}
      />

      {/* Chat modal */}
      <ChatModal
        open={chatOpen}
        initialText={chatInitialText}
        onClose={handleCloseChat}
        onOpenCivic={handleChatCivicHandoff}
      />
    </div>
  );
}
