/**
 * Phase 6 — AI Chat and Decision-Support Agent Types
 *
 * Aligned strictly with backend Pydantic schemas:
 * - backend/app/schemas/chat.py
 * - backend/app/schemas/agent.py
 * - backend/app/safety/states.py
 */

export type SafetyStatus = 'CLEAR' | 'CONCERNING' | 'EMERGENCY';

export type MessageSenderRole = 'USER' | 'ASSISTANT' | 'SYSTEM';

export interface ChatSessionCreate {
  mother_id?: string;
  title?: string;
  language?: string;
}

export interface ChatSessionResponse {
  id: string;
  mother_id: string;
  title?: string | null;
  language: string;
  created_at: string;
}

export interface ChatMessageCreate {
  content: string;
  language?: string;
}

export interface MessageItem {
  id: string;
  session_id: string;
  sender_role: MessageSenderRole;
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface ChatTurnResponse {
  session_id: string;
  user_message: MessageItem;
  assistant_message: MessageItem;
  safety_state: SafetyStatus;
  safety_events: string[];
  disclaimer: string;
}

export type AgentToolName =
  | 'get_health_summary'
  | 'get_recent_vitals'
  | 'get_recent_symptoms'
  | 'check_safety_alerts'
  | 'get_upcoming_visits'
  | 'explain_risk_factors';

export type ToolExecutionStatus = 'SUCCESS' | 'SKIPPED' | 'DENIED';

export interface AgentToolExecution {
  tool_name: AgentToolName;
  status: ToolExecutionStatus;
  summary?: string | null;
  data?: Record<string, unknown> | null;
}

export interface AgentQueryRequest {
  mother_id?: string;
  query: string;
  requested_tools?: AgentToolName[];
  language?: string;
}

export interface AgentQueryResponse {
  mother_id: string;
  query: string;
  response: string;
  safety_state: SafetyStatus;
  tools_invoked: AgentToolExecution[];
  disclaimer: string;
  created_at: string;
}
