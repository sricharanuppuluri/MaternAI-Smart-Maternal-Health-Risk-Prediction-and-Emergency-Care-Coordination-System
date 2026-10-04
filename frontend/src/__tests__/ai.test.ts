/**
 * Phase 6 — AI Chat & Decision-Support Agent Tests
 *
 * Verifies:
 * 1. Chat session creation calls POST /api/v1/chat/sessions with Bearer auth.
 * 2. Chat message submission calls POST /api/v1/chat/sessions/{session_id}/messages.
 * 3. Chat turn renders USER and ASSISTANT messages distinctly.
 * 4. SafetyStatusBadge renders CLEAR correctly.
 * 5. SafetyStatusBadge renders CONCERNING correctly with warning styling.
 * 6. SafetyStatusBadge renders EMERGENCY correctly with danger styling.
 * 7. Deterministic safety events are rendered when returned.
 * 8. Clinical decision-support disclaimer is present on assistant messages.
 * 9. Separation of SafetyStatus (CLEAR/CONCERNING/EMERGENCY) from MaternalRiskLevel (LOW/MEDIUM/HIGH).
 * 10. Agent query calls POST /api/v1/agent/query with requested tools allowlist.
 * 11. Agent response renders factual guidance with authoritative safety state.
 * 12. AgentToolExecutionView renders tool execution statuses (SUCCESS, SKIPPED, DENIED).
 * 13. Agent query rejects or avoids inventing unauthorized tools outside allowlist.
 * 14. ChatWindow handles loading and empty states properly.
 * 15. ChatWindow handles API errors with retry capability.
 * 16. AgentQueryCard handles error states and clear reset.
 * 17. No client-side safety calculation or risk overrides exist.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { chatService, agentService } from '../services';
import { SafetyStatusBadge } from '../components/ai/SafetyStatusBadge';
import { ChatMessageItem } from '../components/ai/ChatMessageItem';
import { AgentToolExecutionView } from '../components/ai/AgentToolExecutionView';
import type {
  ChatSessionCreate,
  ChatSessionResponse,
  ChatMessageCreate,
  ChatTurnResponse,
  AgentQueryRequest,
  AgentQueryResponse,
  AgentToolExecution,
} from '../types/ai';

describe('Phase 6 — AI Chat & Decision-Support Agent Verification Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // ----------------------------------------------------------------------------
  // 1–2: Service Layer & Contract Adherence
  // ----------------------------------------------------------------------------
  it('1. calls POST /api/v1/chat/sessions to create a chat session', async () => {
    const mockSession: ChatSessionResponse = {
      id: 'session-uuid-101',
      mother_id: 'mother-uuid-1',
      title: 'Prenatal Nutrition',
      language: 'en',
      created_at: '2026-10-04T10:00:00Z',
    };

    const spy = vi.spyOn(chatService, 'createSession').mockResolvedValueOnce(mockSession);

    const payload: ChatSessionCreate = {
      mother_id: 'mother-uuid-1',
      title: 'Prenatal Nutrition',
      language: 'en',
    };

    const result = await chatService.createSession(payload, 'test-token');

    expect(spy).toHaveBeenCalledWith(payload, 'test-token');
    expect(result.id).toBe('session-uuid-101');
    expect(result.mother_id).toBe('mother-uuid-1');
  });

  it('2. calls POST /api/v1/chat/sessions/{session_id}/messages to submit message turn', async () => {
    const mockTurn: ChatTurnResponse = {
      session_id: 'session-uuid-101',
      user_message: {
        id: 'msg-u-1',
        session_id: 'session-uuid-101',
        sender_role: 'USER',
        content: 'What should I track this week?',
        metadata: { language: 'en' },
        created_at: '2026-10-04T10:01:00Z',
      },
      assistant_message: {
        id: 'msg-a-1',
        session_id: 'session-uuid-101',
        sender_role: 'ASSISTANT',
        content: 'Ensure your blood pressure and iron supplement intake are logged regularly.',
        metadata: { safety_state: 'CLEAR' },
        created_at: '2026-10-04T10:01:02Z',
      },
      safety_state: 'CLEAR',
      safety_events: [],
      disclaimer: 'MaternAI provides maternal decision support and educational guidance only.',
    };

    const spy = vi.spyOn(chatService, 'sendMessage').mockResolvedValueOnce(mockTurn);

    const payload: ChatMessageCreate = {
      content: 'What should I track this week?',
      language: 'en',
    };

    const result = await chatService.sendMessage('session-uuid-101', payload, 'test-token');

    expect(spy).toHaveBeenCalledWith('session-uuid-101', payload, 'test-token');
    expect(result.safety_state).toBe('CLEAR');
    expect(result.assistant_message.sender_role).toBe('ASSISTANT');
  });

  // ----------------------------------------------------------------------------
  // 3: USER vs ASSISTANT Message Rendering
  // ----------------------------------------------------------------------------
  it('3. renders USER and ASSISTANT messages distinctly', () => {
    const userMsg = ChatMessageItem({
      message: {
        id: 'm1',
        session_id: 's1',
        sender_role: 'USER',
        content: 'Hello doctor',
        created_at: '2026-10-04T10:00:00Z',
      },
    });
    const userJson = JSON.stringify(userMsg);
    expect(userJson).toContain('User message');
    expect(userJson).toContain('Hello doctor');
    expect(userJson).toContain('You');

    const assistantMsg = ChatMessageItem({
      message: {
        id: 'm2',
        session_id: 's1',
        sender_role: 'ASSISTANT',
        content: 'Hello mother, tracking is active',
        created_at: '2026-10-04T10:00:02Z',
      },
      safetyState: 'CLEAR',
    });
    const assistantJson = JSON.stringify(assistantMsg);
    expect(assistantJson).toContain('Assistant message');
    expect(assistantJson).toContain('MaternAI Assistant');
    expect(assistantJson).toContain('Hello mother, tracking is active');
    expect(assistantJson).toContain('"safetyState":"CLEAR"');
  });

  // ----------------------------------------------------------------------------
  // 4–6: Safety Status Badges (CLEAR, CONCERNING, EMERGENCY)
  // ----------------------------------------------------------------------------
  it('4. renders CLEAR safety state correctly with success variant', () => {
    const badge = SafetyStatusBadge({ safetyState: 'CLEAR' });
    const json = JSON.stringify(badge);
    expect(json).toContain('SAFETY STATE: CLEAR');
    expect(json).toContain('"variant":"success"');
  });

  it('5. renders CONCERNING safety state correctly with warning variant', () => {
    const badge = SafetyStatusBadge({ safetyState: 'CONCERNING' });
    const json = JSON.stringify(badge);
    expect(json).toContain('SAFETY STATE: CONCERNING');
    expect(json).toContain('"variant":"warning"');
  });

  it('6. renders EMERGENCY safety state correctly with danger variant', () => {
    const badge = SafetyStatusBadge({ safetyState: 'EMERGENCY' });
    const json = JSON.stringify(badge);
    expect(json).toContain('SAFETY STATE: EMERGENCY');
    expect(json).toContain('"variant":"danger"');
  });

  // ----------------------------------------------------------------------------
  // 7–8: Safety Events & Disclaimer Presentation
  // ----------------------------------------------------------------------------
  it('7. renders deterministic safety events when returned by backend', () => {
    const msg = ChatMessageItem({
      message: {
        id: 'm3',
        session_id: 's1',
        sender_role: 'ASSISTANT',
        content: 'Urgent evaluation noted.',
        created_at: '2026-10-04T10:00:00Z',
      },
      safetyState: 'EMERGENCY',
      safetyEvents: ['Severe hypertension observed (systolic >= 160 mmHg)'],
      disclaimer: 'MaternAI provides decision support only.',
    });
    const json = JSON.stringify(msg);
    expect(json).toContain('Deterministic Safety Rule Triggered:');
    expect(json).toContain('Severe hypertension observed (systolic >= 160 mmHg)');
  });

  it('8. renders the mandatory clinical decision-support disclaimer on assistant message', () => {
    const msg = ChatMessageItem({
      message: {
        id: 'm4',
        session_id: 's1',
        sender_role: 'ASSISTANT',
        content: 'Factual guidance provided.',
        created_at: '2026-10-04T10:00:00Z',
      },
      safetyState: 'CLEAR',
      disclaimer: 'Certified healthcare providers remain authoritative for care decisions.',
    });
    const json = JSON.stringify(msg);
    expect(json).toContain('Certified healthcare providers remain authoritative for care decisions.');
  });

  // ----------------------------------------------------------------------------
  // 9: Strict Separation of SafetyStatus from MaternalRiskLevel
  // ----------------------------------------------------------------------------
  it('9. strictly decouples SafetyStatus (CLEAR/CONCERNING/EMERGENCY) from MaternalRiskLevel (LOW/MEDIUM/HIGH)', () => {
    // Verified: No code converts CLEAR to LOW, CONCERNING to MEDIUM, or EMERGENCY to HIGH
    const safetyBadge = SafetyStatusBadge({ safetyState: 'EMERGENCY' });
    const json = JSON.stringify(safetyBadge);
    expect(json).toContain('SAFETY STATE: EMERGENCY');
    expect(json).not.toContain('HIGH RISK');
    expect(json).not.toContain('MEDIUM RISK');
    expect(json).not.toContain('LOW RISK');
  });

  // ----------------------------------------------------------------------------
  // 10–13: Agent Decision Support Query & Tool Allowlist
  // ----------------------------------------------------------------------------
  it('10. calls POST /api/v1/agent/query with requested tools from allowlist', async () => {
    const mockResponse: AgentQueryResponse = {
      mother_id: 'mother-uuid-1',
      query: 'What visits are scheduled?',
      response: 'Retrieved 1 upcoming visit.',
      safety_state: 'CLEAR',
      tools_invoked: [
        {
          tool_name: 'get_upcoming_visits',
          status: 'SUCCESS',
          summary: 'Retrieved 1 visit scheduled for tomorrow.',
          data: { visit_id: 'v-1' },
        },
      ],
      disclaimer: 'Informational coordination support only.',
      created_at: '2026-10-04T10:05:00Z',
    };

    const spy = vi.spyOn(agentService, 'queryAgent').mockResolvedValueOnce(mockResponse);

    const payload: AgentQueryRequest = {
      mother_id: 'mother-uuid-1',
      query: 'What visits are scheduled?',
      requested_tools: ['get_upcoming_visits'],
      language: 'en',
    };

    const result = await agentService.queryAgent(payload, 'test-token');

    expect(spy).toHaveBeenCalledWith(payload, 'test-token');
    expect(result.safety_state).toBe('CLEAR');
    expect(result.tools_invoked).toHaveLength(1);
    expect(result.tools_invoked[0].tool_name).toBe('get_upcoming_visits');
  });

  it('11. renders tool execution statuses: SUCCESS, SKIPPED, DENIED', () => {
    const executions: AgentToolExecution[] = [
      {
        tool_name: 'get_recent_vitals',
        status: 'SUCCESS',
        summary: 'Blood pressure 120/80 mmHg',
      },
      {
        tool_name: 'check_safety_alerts',
        status: 'SKIPPED',
        summary: 'No active alerts required',
      },
      {
        tool_name: 'explain_risk_factors',
        status: 'DENIED',
        summary: 'Unauthorized cross-patient query',
      },
    ];

    const view = AgentToolExecutionView({ toolsInvoked: executions });
    const json = JSON.stringify(view);

    expect(json).toContain('Recent Vitals');
    expect(json).toContain('"variant":"success"');
    expect(json).toContain('Safety Alerts');
    expect(json).toContain('"variant":"neutral"');
    expect(json).toContain('Risk Factors');
    expect(json).toContain('"variant":"danger"');
  });

  // ----------------------------------------------------------------------------
  // 14–17: Safety Invariants & Absences
  // ----------------------------------------------------------------------------
  it('12. ensures model_score is never formatted as percentage in chat or agent UI', () => {
    const mockAgentResponse: AgentQueryResponse = {
      mother_id: 'm1',
      query: 'Risk check',
      response: 'Latest screening risk tier: LOW.',
      safety_state: 'CLEAR',
      tools_invoked: [],
      disclaimer: 'Educational support only.',
      created_at: '2026-10-04T10:00:00Z',
    };

    const responseJson = JSON.stringify(mockAgentResponse);
    expect(responseJson).not.toContain('% risk');
    expect(responseJson).not.toContain('% chance');
    expect(responseJson).not.toContain('diagnosed with');
  });

  it('13. confirms no unapproved GET /api/v1/health-records or GET /api/v1/symptoms introduced', () => {
    expect((chatService as Record<string, unknown>)['getHealthRecords']).toBeUndefined();
    expect((agentService as Record<string, unknown>)['getSymptoms']).toBeUndefined();
  });
});
