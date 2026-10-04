/**
 * Agent Query Card component.
 *
 * Coordinates:
 * - Submitting queries to POST /api/v1/agent/query
 * - Tool selection strictly limited to the backend authorized allowlist
 * - Presenting authoritative safety_state from the backend SafetyEngine
 * - Rendering tools_invoked execution results (SUCCESS, SKIPPED, DENIED)
 * - Factual response presentation with decision-support disclaimer
 */

import React, { useState } from 'react';
import { Card, Button, AlertBanner } from '../common';
import { SafetyStatusBadge } from './SafetyStatusBadge';
import { AgentToolExecutionView } from './AgentToolExecutionView';
import { agentService } from '../../services/agentService';
import type {
  AgentToolName,
  AgentQueryResponse,
} from '../../types/ai';

export interface AgentQueryCardProps {
  motherId?: string;
  className?: string;
}

const AUTHORIZED_TOOLS: { name: AgentToolName; label: string; description: string }[] = [
  {
    name: 'get_health_summary',
    label: 'Health Summary',
    description: 'Maternal profile, baseline gestational age, and assigned ASHA',
  },
  {
    name: 'get_recent_vitals',
    label: 'Recent Vitals',
    description: 'Recent blood pressure, glucose, and heart rate observations',
  },
  {
    name: 'get_recent_symptoms',
    label: 'Recent Symptoms',
    description: 'Reported symptoms and clinical observations',
  },
  {
    name: 'check_safety_alerts',
    label: 'Safety Alerts',
    description: 'Active safety events and coordination alerts',
  },
  {
    name: 'get_upcoming_visits',
    label: 'Upcoming Visits',
    description: 'Scheduled home visits and pending follow-up checks',
  },
  {
    name: 'explain_risk_factors',
    label: 'Explain Risk Factors',
    description: 'Contributing factors from the latest ML screening evaluation',
  },
];

export const AgentQueryCard: React.FC<AgentQueryCardProps> = ({
  motherId,
  className = '',
}) => {
  const [query, setQuery] = useState<string>('');
  const [selectedTools, setSelectedTools] = useState<AgentToolName[]>([
    'get_health_summary',
    'get_upcoming_visits',
  ]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AgentQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const toggleTool = (tool: AgentToolName) => {
    setSelectedTools((prev) =>
      prev.includes(tool) ? prev.filter((t) => t !== tool) : [...prev, tool]
    );
  };

  const handleQuery = async () => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await agentService.queryAgent({
        mother_id: motherId,
        query: query.trim(),
        requested_tools: selectedTools.length > 0 ? selectedTools : undefined,
        language: 'en',
      });
      setResponse(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to query decision-support agent.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card
      title="Decision-Support Agent"
      subtitle="Context-aware reasoning over authorized clinical data & safety alerts"
      className={`agent-query-card space-y-4 ${className}`}
    >
      {/* Query Form */}
      <div className="space-y-3">
        <div>
          <label htmlFor="agent-query-input" className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
            Clinical Question or Coordination Query
          </label>
          <textarea
            id="agent-query-input"
            rows={3}
            placeholder="e.g. What are my upcoming checkups and recent vital trends?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
            className="w-full text-sm p-2 border rounded focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        {/* Authorized Tool Allowlist Selection */}
        <div>
          <span className="block text-xs font-semibold text-muted uppercase tracking-wider mb-2">
            Authorized Agent Tools (Strict Allowlist)
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {AUTHORIZED_TOOLS.map((tool) => {
              const isChecked = selectedTools.includes(tool.name);
              return (
                <label
                  key={tool.name}
                  className={`tool-checkbox-item flex items-start gap-2 p-2 border rounded cursor-pointer text-xs transition-colors ${
                    isChecked ? 'bg-primary-light border-primary' : 'bg-white hover:bg-neutral-light'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleTool(tool.name)}
                    disabled={isLoading}
                    className="mt-0.5"
                  />
                  <div>
                    <span className="font-semibold block">{tool.label}</span>
                    <span className="text-muted text-[11px] leading-tight block">
                      {tool.description}
                    </span>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* Submit Action */}
        <div className="flex items-center gap-3 pt-2">
          <Button
            variant="primary"
            onClick={handleQuery}
            disabled={isLoading || !query.trim()}
            isLoading={isLoading}
          >
            {isLoading ? 'Querying Agent...' : 'Query Decision Agent'}
          </Button>
          {query.trim() && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setQuery('');
                setResponse(null);
                setError(null);
              }}
              disabled={isLoading}
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <AlertBanner
          type="danger"
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Response Display */}
      {response && (
        <div className="agent-response-box mt-4 p-4 border rounded bg-white shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b pb-2">
            <span className="text-xs font-semibold text-muted uppercase">Agent Response</span>
            <SafetyStatusBadge safetyState={response.safety_state} />
          </div>

          <p className="text-sm whitespace-pre-wrap leading-relaxed m-0 text-foreground">
            {response.response}
          </p>

          {/* Invoked Tools Audit */}
          <AgentToolExecutionView toolsInvoked={response.tools_invoked} />

          {/* Decision Support Disclaimer */}
          {response.disclaimer && (
            <p className="agent-disclaimer text-[11px] text-muted italic mt-3 pt-2 border-t m-0">
              {response.disclaimer}
            </p>
          )}
        </div>
      )}
    </Card>
  );
};
