/**
 * Decision-Support Agent API service.
 * Handles queries to the authorized MaternAI decision-support agent.
 * Contract:
 * - POST /api/v1/agent/query
 *
 * Safety & Tool Boundaries:
 * - Only backend-allowlisted tools can be executed.
 * - The returned safety_state (CLEAR, CONCERNING, EMERGENCY) overrides AI reasoning.
 * - Factual tool summaries and results are returned without invented clinical advice.
 */

import { apiRequest } from './apiClient';
import type { AgentQueryRequest, AgentQueryResponse } from '../types/ai';

export const agentService = {
  /**
   * Execute an authorized decision-support query with allowlisted tools.
   * Calls POST /api/v1/agent/query with Bearer token.
   */
  async queryAgent(
    payload: AgentQueryRequest,
    token?: string | null
  ): Promise<AgentQueryResponse> {
    return apiRequest<AgentQueryResponse>('/agent/query', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
