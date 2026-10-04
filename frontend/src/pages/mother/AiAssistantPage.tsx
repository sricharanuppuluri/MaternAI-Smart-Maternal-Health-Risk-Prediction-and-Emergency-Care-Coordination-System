/**
 * AI Assistant Page for Mother Portal.
 *
 * Provides:
 * - Interactive Care Chat via POST /api/v1/chat/sessions & messages
 * - Context-Aware Decision-Support Agent via POST /api/v1/agent/query
 * - Explicit presentation of authoritative SafetyStatus (CLEAR, CONCERNING, EMERGENCY)
 * - Clear separation from ML screening risk tiers (LOW, MEDIUM, HIGH)
 * - Clinical decision-support disclaimers
 */

import React, { useState } from 'react';
import { useAuth } from '../../auth';
import { ChatWindow, AgentQueryCard } from '../../components/ai';
import { VoiceRecorderCard } from '../../components/voice';

export const AiAssistantPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'chat' | 'voice' | 'agent'>('chat');

  return (
    <div className="portal-page ai-assistant-page space-y-4" role="region" aria-labelledby="ai-page-title">
      <header className="page-header mb-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 id="ai-page-title" className="page-title text-2xl font-bold">
            MaternAI Care Assistant & Decision Support
          </h1>
          <p className="page-subtitle text-muted text-sm">
            Conversational maternal guidance and context-aware queries backed by deterministic safety rules.
          </p>
        </div>

        {/* View Mode Switcher */}
        <div className="tab-switcher flex items-center bg-neutral-light p-1 border rounded" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'chat'}
            onClick={() => setActiveTab('chat')}
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
              activeTab === 'chat'
                ? 'bg-white text-primary shadow-sm'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Care Chat
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'voice'}
            onClick={() => setActiveTab('voice')}
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
              activeTab === 'voice'
                ? 'bg-white text-primary shadow-sm'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Voice Assistant
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'agent'}
            onClick={() => setActiveTab('agent')}
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
              activeTab === 'agent'
                ? 'bg-white text-primary shadow-sm'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Decision Agent
          </button>
        </div>
      </header>

      {/* Safety & Educational Guidance Notice */}
      <div className="clinical-guidance-callout p-3 bg-neutral-light border rounded text-xs text-muted">
        <strong>Clinical Safety Notice:</strong> The MaternAI Assistant evaluates conversational inputs through an
        authoritative backend safety engine. Output is for maternal decision support and educational guidance only.
        Certified healthcare providers and assigned ASHA workers remain authoritative for all diagnostic and care decisions.
      </div>

      {/* Main View Area */}
      {activeTab === 'chat' ? (
        <section aria-label="Interactive Care Chat">
          <ChatWindow motherId={user?.id} />
        </section>
      ) : activeTab === 'voice' ? (
        <section aria-label="Multilingual Voice Assistant">
          <VoiceRecorderCard motherId={user?.id} />
        </section>
      ) : (
        <section aria-label="Decision Support Agent">
          <AgentQueryCard motherId={user?.id} />
        </section>
      )}
    </div>
  );
};
