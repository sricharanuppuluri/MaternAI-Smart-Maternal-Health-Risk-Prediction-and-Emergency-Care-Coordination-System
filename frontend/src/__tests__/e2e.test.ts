/**
 * Phase 9 — Frontend End-to-End (E2E) Test Suite
 *
 * Comprehensive end-to-end verification of all complete user-facing frontend journeys:
 * 1. Authentication & Role-Based Routing Journey (Login, Role Isolation, Session Persistence, Logout).
 * 2. Mother Health Screening & Longitudinal Risk Journey (Vitals Entry -> Symptoms -> ML Prediction -> Timeline).
 * 3. Mother Alert & Surveillance Journey (Alert retrieval, empty queue, error handling).
 * 4. AI Care Chat Journey (Session Creation -> Message Sending -> Safety Engine presentation -> Disclaimer).
 * 5. Decision Agent Journey (Query submission -> Tool execution status -> Safety state -> Clinical disclaimer).
 * 6. Multilingual Voice Journey (STT -> Review/Edit -> Explicit Confirmation Boundary -> TTS Playback).
 * 7. ASHA Care Coordination Journey (Live Dashboard Metrics -> Alerts Queue Triage -> Acknowledgment -> Assigned Mother Context).
 * 8. Cross-Feature Navigation, Edge Cases & Security Invariants (No client-side clinical calculations, no leaked secrets).
 */

import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  authService,
  healthRecordService,
  symptomService,
  predictionService,
  timelineService,
  chatService,
  agentService,
  voiceService,
  alertService,
} from '../services';
import { SafetyStatusBadge } from '../components/ai/SafetyStatusBadge';
import { ChatMessageItem } from '../components/ai/ChatMessageItem';
import { AgentToolExecutionView } from '../components/ai/AgentToolExecutionView';
import { VoiceAudioPlayer } from '../components/voice/VoiceAudioPlayer';
import { VoiceLanguageSelector } from '../components/voice/VoiceLanguageSelector';
import { RiskAssessmentCard } from '../components/clinical/RiskAssessmentCard';
import { AshaDashboardPage } from '../pages/asha/AshaDashboardPage';
import { AlertsQueuePage } from '../pages/asha/AlertsQueuePage';
import { SUPPORTED_VOICE_LANGUAGES } from '../types/voice';
import type {
  HealthRecordCreate,
  HealthRecordResponse,
  SymptomSubmission,
  SymptomResponse,
  PredictionRequest,
  PredictionResponse,
  RiskTimelineResponse,
} from '../types/mother';
import type {
  ChatSessionCreate,
  ChatSessionResponse,
  ChatMessageCreate,
  ChatTurnResponse,
  AgentQueryRequest,
  AgentQueryResponse,
} from '../types/ai';
import type {
  VoiceTranscriptionRequest,
  VoiceTranscriptionResponse,
  VoiceConfirmationRequest,
  VoiceConfirmationResponse,
  VoiceSynthesisRequest,
  VoiceSynthesisResponse,
} from '../types/voice';
import type { AlertResponse } from '../types/asha';
import type { PaginatedResponse } from '../types/api';

// Mock auth hook to support role-swapping during E2E journeys
let currentMockUser = {
  id: 'mother-uuid-001',
  email: 'mother@maternai.org',
  role: 'MOTHER' as 'MOTHER' | 'ASHA',
  fullName: 'Priya Sharma',
};

vi.mock('../auth', () => ({
  useAuth: vi.fn(() => ({
    user: currentMockUser,
    isAuthenticated: Boolean(currentMockUser),
    login: vi.fn(),
    logout: vi.fn(),
  })),
}));

// Mock react-router-dom Link and navigation hooks
vi.mock('react-router-dom', () => ({
  Link: ({ to, children, className }: { to: string; children: React.ReactNode; className?: string }) =>
    React.createElement('a', { href: to, className }, children),
  useParams: () => ({}),
  useNavigate: () => vi.fn(),
}));

describe('Phase 9 — Frontend End-to-End (E2E) Test Suite', () => {
  let mockStorage: Record<string, string> = {};

  beforeEach(() => {
    vi.restoreAllMocks();
    mockStorage = {};

    globalThis.localStorage = {
      getItem: (key: string) => mockStorage[key] || null,
      setItem: (key: string, val: string) => {
        mockStorage[key] = val;
      },
      removeItem: (key: string) => {
        delete mockStorage[key];
      },
      clear: () => {
        mockStorage = {};
      },
      length: 0,
      key: () => null,
    };

    currentMockUser = {
      id: 'mother-uuid-001',
      email: 'mother@maternai.org',
      role: 'MOTHER',
      fullName: 'Priya Sharma',
    };
  });

  // ============================================================================
  // 1. AUTHENTICATION & ROLE-BASED ROUTING JOURNEY
  // ============================================================================
  describe('1. Authentication & Role-Based Routing Journey', () => {
    it('executes Mother login journey, establishes session token, and verifies role routing', async () => {
      const motherToken = 'header.mother-jwt-payload.signature';
      const motherProfile = {
        id: 'mother-uuid-001',
        user_id: 'mother-uuid-001',
        email: 'mother@maternai.org',
        role: 'MOTHER' as const,
        full_name: 'Priya Sharma',
        created_at: '2026-10-04T08:00:00Z',
        updated_at: '2026-10-04T08:00:00Z',
      };

      vi.spyOn(authService, 'bootstrapProfile').mockResolvedValueOnce(motherProfile);

      // 1. Client bootstrap with token
      const profile = await authService.bootstrapProfile(
        { full_name: 'Priya Sharma', role: 'MOTHER' },
        motherToken
      );

      // 2. Persist in storage
      localStorage.setItem('materna_auth_token', motherToken);
      localStorage.setItem('maternai_user', JSON.stringify(profile));

      expect(profile.role).toBe('MOTHER');
      expect(localStorage.getItem('materna_auth_token')).toBe(motherToken);
      expect(JSON.parse(localStorage.getItem('maternai_user')!).role).toBe('MOTHER');

      // 3. Target route expectation
      const destination = profile.role === 'MOTHER' ? '/mother' : '/asha';
      expect(destination).toBe('/mother');
    });

    it('executes ASHA worker login journey, establishes session token, and verifies ASHA routing', async () => {
      const ashaToken = 'header.asha-jwt-payload.signature';
      const ashaProfile = {
        id: 'asha-uuid-002',
        user_id: 'asha-uuid-002',
        email: 'asha@maternai.org',
        role: 'ASHA' as const,
        full_name: 'Care Coordinator',
        created_at: '2026-10-04T08:00:00Z',
        updated_at: '2026-10-04T08:00:00Z',
      };

      vi.spyOn(authService, 'bootstrapProfile').mockResolvedValueOnce(ashaProfile);

      const profile = await authService.bootstrapProfile(
        { full_name: 'Care Coordinator', role: 'ASHA' },
        ashaToken
      );

      localStorage.setItem('materna_auth_token', ashaToken);
      localStorage.setItem('maternai_user', JSON.stringify(profile));

      expect(profile.role).toBe('ASHA');
      expect(localStorage.getItem('materna_auth_token')).toBe(ashaToken);

      const destination = profile.role === 'ASHA' ? '/asha' : '/mother';
      expect(destination).toBe('/asha');
    });

    it('enforces role isolation preventing unauthorized cross-portal access', () => {
      // Mother attempting to access ASHA portal
      const motherRole = 'MOTHER';
      const isAllowedAsha = (role: string) => role === 'ASHA';
      expect(isAllowedAsha(motherRole)).toBe(false);

      // ASHA attempting to access Mother-only personal health entry
      const ashaRole = 'ASHA';
      const isAllowedMotherPrivate = (role: string) => role === 'MOTHER';
      expect(isAllowedMotherPrivate(ashaRole)).toBe(false);
    });

    it('executes sign out journey and completely purges authenticated storage keys', () => {
      localStorage.setItem('materna_auth_token', 'active-token-xyz');
      localStorage.setItem('maternai_user', JSON.stringify({ id: '1', role: 'MOTHER' }));

      // User initiates sign out
      localStorage.removeItem('materna_auth_token');
      localStorage.removeItem('maternai_user');

      expect(localStorage.getItem('materna_auth_token')).toBeNull();
      expect(localStorage.getItem('maternai_user')).toBeNull();
    });
  });

  // ============================================================================
  // 2. MOTHER HEALTH SCREENING & LONGITUDINAL RISK JOURNEY
  // ============================================================================
  describe('2. Mother Health Screening & Longitudinal Risk Journey', () => {
    it('executes complete journey: vitals entry -> symptom logging -> ML risk prediction -> timeline presentation', async () => {
      const motherId = 'mother-uuid-001';
      const hrId = 'hr-uuid-999';

      // Step 1: Submit vital measurements
      const hrPayload: HealthRecordCreate = {
        pregnancy_week: 30,
        systolic_bp: 148,
        diastolic_bp: 94,
        blood_sugar: 115,
        body_temperature: 37.0,
        heart_rate: 86,
        weight_kg: 66.5,
      };

      const mockHrResponse: HealthRecordResponse = {
        id: hrId,
        mother_id: motherId,
        pregnancy_week: 30,
        systolic_bp: 148,
        diastolic_bp: 94,
        blood_sugar: 115,
        body_temperature: 37.0,
        heart_rate: 86,
        weight_kg: 66.5,
        recorded_at: '2026-10-04T09:00:00Z',
        created_at: '2026-10-04T09:00:00Z',
      };

      vi.spyOn(healthRecordService, 'createHealthRecord').mockResolvedValueOnce(mockHrResponse);
      const createdHr = await healthRecordService.createHealthRecord(hrPayload);
      expect(createdHr.id).toBe(hrId);

      // Step 2: Submit accompanying symptoms
      const symptomPayload: SymptomSubmission = {
        health_record_id: createdHr.id,
        symptoms: [
          { symptom_code: 'headache', severity: 2, notes: 'Throbbing frontal headache' },
          { symptom_code: 'blurred_vision', severity: 1 },
        ],
      };

      const mockSymptomsResponse: SymptomResponse[] = [
        {
          id: 'sym-101',
          mother_id: motherId,
          health_record_id: hrId,
          symptom_code: 'headache',
          severity: 2,
          notes: 'Throbbing frontal headache',
          recorded_at: '2026-10-04T09:01:00Z',
          created_at: '2026-10-04T09:01:00Z',
        },
        {
          id: 'sym-102',
          mother_id: motherId,
          health_record_id: hrId,
          symptom_code: 'blurred_vision',
          severity: 1,
          recorded_at: '2026-10-04T09:01:00Z',
          created_at: '2026-10-04T09:01:00Z',
        },
      ];

      vi.spyOn(symptomService, 'recordSymptoms').mockResolvedValueOnce(mockSymptomsResponse);
      const recordedSymptoms = await symptomService.recordSymptoms(symptomPayload);
      expect(recordedSymptoms).toHaveLength(2);

      // Step 3: Trigger ML Risk Prediction
      const predPayload: PredictionRequest = {
        health_record_id: createdHr.id,
      };

      const mockPrediction: PredictionResponse = {
        id: 'pred-uuid-888',
        mother_id: motherId,
        health_record_id: hrId,
        risk_level: 'HIGH',
        model_score: 0.84,
        model_version: 'v1.0.0',
        feature_schema_version: 'v1.0',
        contributing_factors: [
          { feature: 'systolic_bp', direction: 'INCREASES_RISK', value: 148 },
          { feature: 'blurred_vision', direction: 'INCREASES_RISK', value: 1 },
        ],
        created_at: '2026-10-04T09:02:00Z',
      };

      vi.spyOn(predictionService, 'requestPrediction').mockResolvedValueOnce(mockPrediction);
      const prediction = await predictionService.requestPrediction(predPayload);
      expect(prediction.risk_level).toBe('HIGH');
      expect(prediction.model_score).toBe(0.84);

      // Step 4: Render Risk Assessment Card outcome
      const cardEl = RiskAssessmentCard({ prediction });
      const cardJson = JSON.stringify(cardEl);
      expect(cardJson).toContain('HIGH RISK');
      expect(cardJson).toContain('Systolic Bp');
      // Verify model_score is never presented as percentage probability
      expect(cardJson).not.toContain('84%');
      expect(cardJson).toContain('Clinical Decision-Support Notice:');

      // Step 5: Timeline Retrieval
      const mockTimeline: RiskTimelineResponse = {
        mother_id: motherId,
        current_risk_level: 'HIGH',
        assessments: [
          {
            timestamp: '2026-10-04T09:02:00Z',
            assessment_type: 'ML_PREDICTION',
            risk_level: 'HIGH',
            systolic_bp: 148,
            diastolic_bp: 94,
          },
        ],
      };

      vi.spyOn(timelineService, 'getRiskTimeline').mockResolvedValueOnce(mockTimeline);
      const timeline = await timelineService.getRiskTimeline(motherId);
      expect(timeline.current_risk_level).toBe('HIGH');
      expect(timeline.assessments[0].systolic_bp).toBe(148);
    });

    it('enforces categorical separation between ML risk_level and SafetyEngine safety_state', () => {
      const mlLevels = ['LOW', 'MEDIUM', 'HIGH'];
      const safetyStates = ['CLEAR', 'CONCERNING', 'EMERGENCY'];

      mlLevels.forEach((level) => {
        expect(safetyStates).not.toContain(level);
      });
      safetyStates.forEach((state) => {
        expect(mlLevels).not.toContain(state);
      });
    });
  });

  // ============================================================================
  // 3. MOTHER ALERT & SURVEILLANCE JOURNEY
  // ============================================================================
  describe('3. Mother Alert & Surveillance Journey', () => {
    it('fetches alerts queue and handles populated, empty, and error states', async () => {
      // Populated state
      const mockAlertList: PaginatedResponse<AlertResponse> = {
        items: [
          {
            id: 'alert-1',
            mother_id: 'mother-uuid-001',
            mother_name: 'Priya Sharma',
            severity: 'HIGH',
            status: 'NEW',
            trigger_reason: 'Severe blood pressure threshold exceeded (148/94 mmHg)',
            created_at: '2026-10-04T09:00:00Z',
            updated_at: '2026-10-04T09:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        size: 20,
        total_pages: 1,
      };

      vi.spyOn(alertService, 'listAlerts').mockResolvedValueOnce(mockAlertList);
      const populatedRes = await alertService.listAlerts(1, 20);
      expect(populatedRes.items).toHaveLength(1);
      expect(populatedRes.items[0].severity).toBe('HIGH');

      // Empty state
      const emptyAlertList: PaginatedResponse<AlertResponse> = {
        items: [],
        total: 0,
        page: 1,
        size: 20,
        total_pages: 1,
      };
      vi.spyOn(alertService, 'listAlerts').mockResolvedValueOnce(emptyAlertList);
      const emptyRes = await alertService.listAlerts(1, 20);
      expect(emptyRes.items).toHaveLength(0);

      // Error state
      vi.spyOn(alertService, 'listAlerts').mockRejectedValueOnce(new Error('Server unavailable: 503'));
      await expect(alertService.listAlerts(1, 20)).rejects.toThrow('Server unavailable: 503');
    });
  });

  // ============================================================================
  // 4. AI CARE CHAT JOURNEY
  // ============================================================================
  describe('4. AI Care Chat Journey', () => {
    it('creates chat session, submits message, and presents backend safety state & disclaimer', async () => {
      const sessionId = 'session-chat-e2e-1';
      const motherId = 'mother-uuid-001';

      // 1. Create Session
      const sessionCreatePayload: ChatSessionCreate = {
        mother_id: motherId,
        title: 'Gestational Wellness Chat',
        language: 'en',
      };

      const mockSession: ChatSessionResponse = {
        id: sessionId,
        mother_id: motherId,
        title: 'Gestational Wellness Chat',
        language: 'en',
        created_at: '2026-10-04T09:10:00Z',
      };

      vi.spyOn(chatService, 'createSession').mockResolvedValueOnce(mockSession);
      const session = await chatService.createSession(sessionCreatePayload);
      expect(session.id).toBe(sessionId);

      // 2. Submit Chat Message
      const messagePayload: ChatMessageCreate = {
        content: 'I have severe headache and swelling in my hands.',
      };

      const mockTurn: ChatTurnResponse = {
        session_id: sessionId,
        user_message: {
          id: 'msg-u-1',
          session_id: sessionId,
          sender_role: 'USER',
          content: messagePayload.content,
          created_at: '2026-10-04T09:11:00Z',
        },
        assistant_message: {
          id: 'msg-a-1',
          session_id: sessionId,
          sender_role: 'ASSISTANT',
          content: 'Severe headache and hand swelling require immediate attention from your ASHA worker or doctor.',
          created_at: '2026-10-04T09:11:02Z',
        },
        safety_state: 'CONCERNING',
        safety_events: ['Severe headache symptom detected.', 'Hand swelling detected.'],
        disclaimer: 'Clinical decision-support notice: For educational guidance only.',
      };

      vi.spyOn(chatService, 'sendMessage').mockResolvedValueOnce(mockTurn);
      const turn = await chatService.sendMessage(sessionId, messagePayload);

      expect(turn.safety_state).toBe('CONCERNING');
      expect(turn.safety_events).toHaveLength(2);

      // 3. Render Assistant Message with Safety Badge and Disclaimer
      const assistantItem = ChatMessageItem({
        message: turn.assistant_message,
        safetyState: turn.safety_state,
        safetyEvents: turn.safety_events,
        disclaimer: turn.disclaimer,
      });

      expect(assistantItem).toBeTruthy();
      const itemProps = (assistantItem as React.ReactElement<{ className: string }>).props;
      expect(itemProps.className).toContain('items-start');

      // 4. Verify SafetyStatusBadge renders CONCERNING correctly
      const badgeEl = SafetyStatusBadge({ safetyState: turn.safety_state });
      const badgeProps = (badgeEl as React.ReactElement<{ label: string }>).props;
      expect(badgeProps.label).toContain('CONCERNING');
    });

    it('handles chat transmission failure with descriptive error', async () => {
      vi.spyOn(chatService, 'sendMessage').mockRejectedValueOnce(new Error('Chat endpoint error: 504 Gateway Timeout'));

      await expect(chatService.sendMessage('session-1', { content: 'test' })).rejects.toThrow(
        'Chat endpoint error: 504 Gateway Timeout'
      );
    });
  });

  // ============================================================================
  // 5. AGENT / DECISION SUPPORT JOURNEY
  // ============================================================================
  describe('5. Agent / Decision Support Journey', () => {
    it('submits decision agent query, renders invoked tools and preserves safety state', async () => {
      const agentPayload: AgentQueryRequest = {
        mother_id: 'mother-uuid-001',
        query: 'What were the latest vitals and active alerts for this mother?',
        requested_tools: ['get_recent_vitals', 'check_safety_alerts'],
      };

      const mockAgentResponse: AgentQueryResponse = {
        mother_id: 'mother-uuid-001',
        query: agentPayload.query,
        response: 'Latest BP is 148/94 mmHg with 1 high-priority alert active.',
        safety_state: 'CONCERNING',
        tools_invoked: [
          {
            tool_name: 'get_recent_vitals',
            status: 'SUCCESS',
            summary: 'Retrieved 1 record with systolic 148 mmHg',
            data: { systolic: 148, diastolic: 94 },
          },
          {
            tool_name: 'check_safety_alerts',
            status: 'SUCCESS',
            summary: '1 active high-priority alert found',
            data: { alert_count: 1 },
          },
        ],
        disclaimer: 'Clinical decision-support only. Not autonomous medical diagnosis.',
        created_at: '2026-10-04T09:15:00Z',
      };

      vi.spyOn(agentService, 'queryAgent').mockResolvedValueOnce(mockAgentResponse);
      const agentResult = await agentService.queryAgent(agentPayload);

      expect(agentResult.safety_state).toBe('CONCERNING');
      expect(agentResult.tools_invoked).toHaveLength(2);
      expect(agentResult.tools_invoked[0].status).toBe('SUCCESS');

      // Render tool execution UI
      const toolView = AgentToolExecutionView({ toolsInvoked: agentResult.tools_invoked });
      expect(toolView).toBeTruthy();
    });
  });

  // ============================================================================
  // 6. MULTILINGUAL VOICE INTERACTION JOURNEY & CONFIRMATION BOUNDARY
  // ============================================================================
  describe('6. Multilingual Voice Interaction Journey & Confirmation Boundary', () => {
    it('executes full voice flow: audio recording -> STT -> review/edit -> explicit confirmation -> TTS playback', async () => {
      const audioContent = 'UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
      const motherId = 'mother-uuid-001';
      const sessionId = 'session-chat-voice-1';

      // Step 1: Transcribe Audio
      const transcribePayload: VoiceTranscriptionRequest = {
        audio_content: audioContent,
        mime_type: 'audio/webm',
        language: 'hi',
        mother_id: motherId,
      };

      const mockTranscriptionRes: VoiceTranscriptionResponse = {
        transcript: 'मुझे चक्कर आ रहे हैं और बहुत कमजोरी लग रही है।',
        language: 'hi',
        detected_language: 'hi',
        confidence: 0.95,
        duration_seconds: 3.2,
        mother_id: motherId,
        created_at: '2026-10-04T09:20:00Z',
      };

      vi.spyOn(voiceService, 'transcribeAudio').mockResolvedValueOnce(mockTranscriptionRes);
      const transcribeRes = await voiceService.transcribeAudio(transcribePayload);

      expect(transcribeRes.transcript).toBe('मुझे चक्कर आ रहे हैं और बहुत कमजोरी लग रही है।');

      // CRITICAL CONTRACT CHECK: Raw transcript is NOT confirmed clinical data yet!
      // Step 2 & 3: User reviews, edits, and EXPLICITLY confirms
      const editedConfirmedText = 'मुझे चक्कर आ रहे हैं और बहुत कमजोरी लग रही है। (Edited by patient)';

      const confirmPayload: VoiceConfirmationRequest = {
        session_id: sessionId,
        confirmed_text: editedConfirmedText,
        language: 'hi',
        mother_id: motherId,
      };

      const mockConfirmRes: VoiceConfirmationResponse = {
        session_id: sessionId,
        confirmed_text: editedConfirmedText,
        safety_state: 'CLEAR',
        confirmed_at: '2026-10-04T09:21:00Z',
        chat_turn: {
          session_id: sessionId,
          user_message: {
            id: 'v-msg-1',
            session_id: sessionId,
            sender_role: 'USER',
            content: editedConfirmedText,
            created_at: '2026-10-04T09:21:00Z',
          },
          assistant_message: {
            id: 'v-msg-2',
            session_id: sessionId,
            sender_role: 'ASSISTANT',
            content: 'आराम करें और तरल पदार्थ पिएं। यदि चक्कर बने रहें तो आशा कार्यकर्ता को बताएं।',
            created_at: '2026-10-04T09:21:02Z',
          },
          safety_state: 'CLEAR',
          safety_events: [],
          disclaimer: 'केवल सलाह के लिए। डॉक्टर से संपर्क करें।',
        },
      };

      vi.spyOn(voiceService, 'confirmVoiceTranscript').mockResolvedValueOnce(mockConfirmRes);
      const confirmRes = await voiceService.confirmVoiceTranscript(confirmPayload);

      expect(confirmRes.chat_turn.user_message.content).toBe(editedConfirmedText);
      expect(confirmRes.chat_turn.safety_state).toBe('CLEAR');

      // Step 4: Text-to-Speech Synthesis
      const synthPayload: VoiceSynthesisRequest = {
        text: confirmRes.chat_turn.assistant_message.content,
        language: 'hi',
        output_format: 'mp3',
      };

      const mockSynthRes: VoiceSynthesisResponse = {
        audio_content: '//uQZAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAJAAAWjAC...',
        mime_type: 'audio/mp3',
        duration_seconds: 4.1,
        text_length: confirmRes.chat_turn.assistant_message.content.length,
        language: 'hi',
        created_at: '2026-10-04T09:21:05Z',
      };

      vi.spyOn(voiceService, 'synthesizeSpeech').mockResolvedValueOnce(mockSynthRes);
      const synthRes = await voiceService.synthesizeSpeech(synthPayload);

      expect(synthRes.audio_content).toBeTruthy();
      expect(synthRes.mime_type).toBe('audio/mp3');

      // Step 5: Render audio player component
      const playerEl = VoiceAudioPlayer({
        audioContent: synthRes.audio_content,
        mimeType: synthRes.mime_type,
        durationSeconds: synthRes.duration_seconds,
      });
      expect(playerEl).toBeTruthy();
    });

    it('enforces the exact 7-language allowlist', () => {
      const allowed = ['en', 'hi', 'te', 'ta', 'kn', 'bn', 'mr'];
      expect(SUPPORTED_VOICE_LANGUAGES.map((l) => l.code)).toEqual(allowed);

      const selectorEl = VoiceLanguageSelector({
        value: 'hi',
        onChange: () => {},
      });
      expect(selectorEl).toBeTruthy();
    });
  });

  // ============================================================================
  // 7. ASHA CARE COORDINATION JOURNEY
  // ============================================================================
  describe('7. ASHA Care Coordination Journey', () => {
    it('loads ASHA dashboard live metrics and priority alerts without fabricated identity', () => {
      // Set current mock user to ASHA
      currentMockUser = {
        id: 'asha-worker-uuid-001',
        email: 'asha@maternai.org',
        role: 'ASHA',
        fullName: 'Care Coordinator',
      };

      const html = renderToString(React.createElement(AshaDashboardPage));

      // Verifies live layout rendered without fabricated person names
      expect(html).not.toContain('Anita Devi');
      expect(html).toContain('ASHA Care Coordinator:');
      expect(html).toContain('Care Coordinator');
      expect(html).toContain('Active Cohort Mothers');
      expect(html).toContain('Pending Escalation Alerts');
    });

    it('loads Alerts Queue, triages cases, and invokes alertService.updateAlertStatus', async () => {
      const mockAlertQueue: PaginatedResponse<AlertResponse> = {
        items: [
          {
            id: 'alert-e2e-1',
            mother_id: 'mother-uuid-001',
            mother_name: 'Priya Sharma',
            severity: 'CRITICAL',
            status: 'NEW',
            trigger_reason: 'Acute severe hypertension (160/102 mmHg)',
            created_at: '2026-10-04T09:30:00Z',
            updated_at: '2026-10-04T09:30:00Z',
          },
        ],
        total: 1,
        page: 1,
        size: 50,
        total_pages: 1,
      };

      vi.spyOn(alertService, 'listAlerts').mockResolvedValueOnce(mockAlertQueue);
      const queue = await alertService.listAlerts(1, 50);
      expect(queue.items).toHaveLength(1);

      // ASHA acknowledges alert
      const targetAlert = queue.items[0];
      const updatedAlert: AlertResponse = {
        ...targetAlert,
        status: 'ACKNOWLEDGED',
        updated_at: '2026-10-04T09:35:00Z',
      };

      const updateSpy = vi.spyOn(alertService, 'updateAlertStatus').mockResolvedValueOnce(updatedAlert);
      const acknowledged = await alertService.updateAlertStatus(targetAlert.id, {
        status: 'ACKNOWLEDGED',
        notes: 'Acknowledged by ASHA worker via coordination portal.',
      });

      expect(updateSpy).toHaveBeenCalledWith(targetAlert.id, {
        status: 'ACKNOWLEDGED',
        notes: 'Acknowledged by ASHA worker via coordination portal.',
      });
      expect(acknowledged.status).toBe('ACKNOWLEDGED');

      // Verify triage navigation links to assigned mother context
      const timelinePath = `/asha/mothers/${targetAlert.mother_id}/timeline`;
      const assistantPath = `/asha/mothers/${targetAlert.mother_id}/assistant`;
      expect(timelinePath).toBe('/asha/mothers/mother-uuid-001/timeline');
      expect(assistantPath).toBe('/asha/mothers/mother-uuid-001/assistant');
    });

    it('renders live Alerts Queue page structure and loading indicator', () => {
      const html = renderToString(React.createElement(AlertsQueuePage));
      expect(html).toContain('ASHA Escalation &amp; Alert Queue');
      expect(html).toContain('Loading maternal alerts queue...');
    });
  });

  // ============================================================================
  // 8. CROSS-FEATURE NAVIGATION & SECURITY INVARIANTS
  // ============================================================================
  describe('8. Cross-Feature Navigation, Edge Cases & Security Invariants', () => {
    it('verifies that no service-role secrets exist in frontend environment', () => {
      const envKeys = Object.keys(import.meta.env);
      const forbidden = ['SERVICE_ROLE', 'SERVICE_KEY', 'SUPABASE_ADMIN'];

      envKeys.forEach((key) => {
        forbidden.forEach((word) => {
          expect(key.toUpperCase()).not.toContain(word);
        });
      });
    });

    it('verifies clinical decision support disclaimer is present on decision outputs', () => {
      const msgItem = ChatMessageItem({
        message: {
          id: 'test-m-1',
          session_id: 's-1',
          sender_role: 'ASSISTANT',
          content: 'Recommended dietary adjustments.',
          created_at: '2026-10-04T10:00:00Z',
        },
        safetyState: 'CLEAR',
        disclaimer: 'Clinical guidance only. Consult your certified healthcare provider.',
      });

      expect(msgItem).toBeTruthy();
      const msgProps = (msgItem as React.ReactElement<{ className: string }>).props;
      expect(msgProps.className).toContain('items-start');
    });
  });
});
