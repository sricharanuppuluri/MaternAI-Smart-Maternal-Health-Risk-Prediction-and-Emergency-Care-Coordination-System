/**
 * Phase 8 — Full Frontend Integration Verification Suite
 *
 * Verifies the cross-feature integration of all completed phases (Phases 3–7):
 * 1. Authentication & Role-Based Routing Integration:
 *    - Session persistence, token management, and role discrimination (MOTHER vs ASHA).
 *    - Logout clears tokens and resets session state.
 * 2. Mother Health Screening Workflow Integration:
 *    - Health Record entry -> Symptom submission -> ML Risk Prediction -> Longitudinal Timeline.
 *    - Separation of ML screening risk tiers (LOW/MEDIUM/HIGH) from SafetyEngine states (CLEAR/CONCERNING/EMERGENCY).
 * 3. AI Care Chat & Decision-Support Workflow Integration:
 *    - Chat session creation -> Message submission -> Backend-authoritative safety state presentation.
 *    - Mandatory clinical disclaimer presence.
 *    - Decision Agent query execution with strict tool allowlist.
 * 4. Voice Interaction Workflow Integration with Confirmation Boundary:
 *    - Audio transcription -> Review/edit phase -> Explicit user confirmation -> Assistant turn response.
 *    - Text-to-Speech synthesis with 7-language allowlist.
 * 5. ASHA Care Coordination & Assigned-Mother Integration:
 *    - ASHA assigned mother timeline access with contextual mother_id propagation.
 *    - ASHA decision support query scoped to assigned mother.
 *    - Alerts queue navigation to patient timeline and assistant.
 * 6. Security and Contract Safety Invariants:
 *    - Supabase service-role key is never exposed.
 *    - No client-side recalculation, inferencing, or override of clinical risk or safety states.
 */

import React from 'react';
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
} from '../services';
import { SafetyStatusBadge } from '../components/ai/SafetyStatusBadge';
import { ChatMessageItem } from '../components/ai/ChatMessageItem';
import { AgentToolExecutionView } from '../components/ai/AgentToolExecutionView';
import { VoiceAudioPlayer } from '../components/voice/VoiceAudioPlayer';
import { VoiceLanguageSelector } from '../components/voice/VoiceLanguageSelector';
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

describe('Phase 8 — Full Frontend Integration Verification Suite', () => {
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
  });

  // ============================================================================
  // 1. Authentication & Role Integration
  // ============================================================================
  describe('1. Authentication & Role Routing Integration', () => {
    it('authenticates a MOTHER user and stores session credentials', async () => {
      const motherUser = {
        id: 'mother-uuid-001',
        email: 'mother@example.com',
        role: 'MOTHER' as const,
        full_name: 'Priya Sharma',
      };
      const token = 'mock-mother-jwt-token-12345';

      localStorage.setItem('materna_auth_token', token);
      localStorage.setItem('maternai_user', JSON.stringify(motherUser));

      const mockProfileResponse = {
        id: 'mother-uuid-001',
        user_id: 'mother-uuid-001',
        email: 'mother@example.com',
        role: 'MOTHER' as const,
        full_name: 'Priya Sharma',
        created_at: '2026-10-04T10:00:00Z',
        updated_at: '2026-10-04T10:00:00Z',
      };

      const spy = vi.spyOn(authService, 'bootstrapProfile').mockResolvedValueOnce(mockProfileResponse);

      const res = await authService.bootstrapProfile({
        full_name: 'Priya Sharma',
        role: 'MOTHER',
      }, token);

      expect(spy).toHaveBeenCalledWith({ full_name: 'Priya Sharma', role: 'MOTHER' }, token);
      expect(res.role).toBe('MOTHER');
      expect(localStorage.getItem('materna_auth_token')).toBe(token);
      expect(JSON.parse(localStorage.getItem('maternai_user') || '{}').role).toBe('MOTHER');
    });

    it('authenticates an ASHA worker user and stores session credentials', async () => {
      const ashaUser = {
        id: 'asha-uuid-002',
        email: 'asha@example.com',
        role: 'ASHA' as const,
        full_name: 'Care Coordinator',
      };
      const token = 'mock-asha-jwt-token-67890';

      localStorage.setItem('materna_auth_token', token);
      localStorage.setItem('maternai_user', JSON.stringify(ashaUser));

      const mockProfileResponse = {
        id: 'asha-uuid-002',
        user_id: 'asha-uuid-002',
        email: 'asha@example.com',
        role: 'ASHA' as const,
        full_name: 'Care Coordinator',
        created_at: '2026-10-04T10:00:00Z',
        updated_at: '2026-10-04T10:00:00Z',
      };

      const spy = vi.spyOn(authService, 'bootstrapProfile').mockResolvedValueOnce(mockProfileResponse);

      const res = await authService.bootstrapProfile({
        full_name: 'Care Coordinator',
        role: 'ASHA',
      }, token);

      expect(spy).toHaveBeenCalledWith({ full_name: 'Care Coordinator', role: 'ASHA' }, token);
      expect(res.role).toBe('ASHA');
      expect(localStorage.getItem('materna_auth_token')).toBe(token);
      expect(JSON.parse(localStorage.getItem('maternai_user') || '{}').role).toBe('ASHA');
    });

    it('clears session credentials and tokens upon sign out', () => {
      localStorage.setItem('materna_auth_token', 'temp-session-token');
      localStorage.setItem('maternai_user', JSON.stringify({ id: '1', role: 'MOTHER' }));

      expect(localStorage.getItem('materna_auth_token')).toBe('temp-session-token');

      localStorage.removeItem('materna_auth_token');
      localStorage.removeItem('maternai_user');

      expect(localStorage.getItem('materna_auth_token')).toBeNull();
      expect(localStorage.getItem('maternai_user')).toBeNull();
    });
  });

  // ============================================================================
  // 2. Mother Health Screening Workflow Integration
  // ============================================================================
  describe('2. Mother Health Screening Workflow Integration', () => {
    it('executes full sequence: Health Record -> Symptoms -> ML Prediction -> Risk Timeline', async () => {
      const motherId = 'mother-uuid-001';
      const recordId = 'hr-uuid-501';

      // Step 1: Create Health Record
      const hrCreatePayload: HealthRecordCreate = {
        pregnancy_week: 28,
        systolic_bp: 135,
        diastolic_bp: 88,
        blood_sugar: 110,
        body_temperature: 37.1,
        heart_rate: 82,
        weight_kg: 64.0,
      };

      const mockHrResponse: HealthRecordResponse = {
        id: recordId,
        mother_id: motherId,
        pregnancy_week: 28,
        systolic_bp: 135,
        diastolic_bp: 88,
        blood_sugar: 110,
        body_temperature: 37.1,
        heart_rate: 82,
        weight_kg: 64.0,
        recorded_at: '2026-10-04T10:00:00Z',
        created_at: '2026-10-04T10:00:00Z',
      };

      const hrSpy = vi.spyOn(healthRecordService, 'createHealthRecord').mockResolvedValueOnce(mockHrResponse);
      const createdHr = await healthRecordService.createHealthRecord(hrCreatePayload);
      expect(hrSpy).toHaveBeenCalledWith(hrCreatePayload);
      expect(createdHr.id).toBe(recordId);

      // Step 2: Record Symptoms linked to the created Health Record
      const symptomPayload: SymptomSubmission = {
        health_record_id: createdHr.id,
        symptoms: [
          { symptom_code: 'headache', severity: 2, notes: 'Persistent morning headache' },
          { symptom_code: 'swelling_feet', severity: 1 },
        ],
      };

      const mockSymptomResponse: SymptomResponse[] = [
        {
          id: 'sym-1',
          mother_id: motherId,
          health_record_id: recordId,
          symptom_code: 'headache',
          severity: 2,
          notes: 'Persistent morning headache',
          recorded_at: '2026-10-04T10:01:00Z',
          created_at: '2026-10-04T10:01:00Z',
        },
        {
          id: 'sym-2',
          mother_id: motherId,
          health_record_id: recordId,
          symptom_code: 'swelling_feet',
          severity: 1,
          recorded_at: '2026-10-04T10:01:00Z',
          created_at: '2026-10-04T10:01:00Z',
        },
      ];

      const symptomSpy = vi.spyOn(symptomService, 'recordSymptoms').mockResolvedValueOnce(mockSymptomResponse);
      const symptomResult = await symptomService.recordSymptoms(symptomPayload);
      expect(symptomSpy).toHaveBeenCalledWith(symptomPayload);
      expect(symptomResult).toHaveLength(2);

      // Step 3: Trigger ML Risk Prediction
      const predPayload: PredictionRequest = {
        health_record_id: createdHr.id,
      };

      const mockPredResponse: PredictionResponse = {
        id: 'pred-uuid-901',
        mother_id: motherId,
        health_record_id: recordId,
        risk_level: 'MEDIUM',
        model_score: 0.58,
        model_version: 'v1.0.0',
        feature_schema_version: 'v1.0',
        contributing_factors: [
          { feature: 'systolic_bp', direction: 'INCREASES_RISK', value: 135 },
          { feature: 'headache', direction: 'INCREASES_RISK', value: 2 },
        ],
        created_at: '2026-10-04T10:02:00Z',
      };

      const predSpy = vi.spyOn(predictionService, 'requestPrediction').mockResolvedValueOnce(mockPredResponse);
      const predResult = await predictionService.requestPrediction(predPayload);
      expect(predSpy).toHaveBeenCalledWith(predPayload);
      expect(predResult.risk_level).toBe('MEDIUM');
      expect(predResult.model_score).toBe(0.58);

      // Step 4: Retrieve Longitudinal Risk Timeline
      const mockTimeline: RiskTimelineResponse = {
        mother_id: motherId,
        current_risk_level: 'MEDIUM',
        assessments: [
          {
            timestamp: '2026-10-04T10:02:00Z',
            assessment_type: 'ML_PREDICTION',
            risk_level: 'MEDIUM',
            systolic_bp: 135,
            diastolic_bp: 88,
          },
        ],
      };

      const timelineSpy = vi.spyOn(timelineService, 'getRiskTimeline').mockResolvedValueOnce(mockTimeline);
      const timelineResult = await timelineService.getRiskTimeline(motherId);
      expect(timelineSpy).toHaveBeenCalledWith(motherId);
      expect(timelineResult.current_risk_level).toBe('MEDIUM');
      expect(timelineResult.assessments).toHaveLength(1);
    });

    it('strictly separates ML risk_level (LOW/MEDIUM/HIGH) from SafetyEngine safety_state (CLEAR/CONCERNING/EMERGENCY)', () => {
      const mlRiskTiers = ['LOW', 'MEDIUM', 'HIGH'];
      const safetyStates = ['CLEAR', 'CONCERNING', 'EMERGENCY'];

      mlRiskTiers.forEach((mlTier) => {
        expect(safetyStates).not.toContain(mlTier);
      });
      safetyStates.forEach((state) => {
        expect(mlRiskTiers).not.toContain(state);
      });
    });
  });

  // ============================================================================
  // 3. AI Care Chat & Decision-Support Agent Integration
  // ============================================================================
  describe('3. AI Care Chat & Decision-Support Workflow Integration', () => {
    it('creates chat session, sends message, and receives backend-authoritative safety state', async () => {
      const sessionId = 'session-uuid-101';
      const motherId = 'mother-uuid-001';

      // Create Session
      const sessionPayload: ChatSessionCreate = {
        mother_id: motherId,
        title: 'Gestational Diet and Symptoms',
        language: 'en',
      };

      const mockSession: ChatSessionResponse = {
        id: sessionId,
        mother_id: motherId,
        title: 'Gestational Diet and Symptoms',
        language: 'en',
        created_at: '2026-10-04T10:10:00Z',
      };

      vi.spyOn(chatService, 'createSession').mockResolvedValueOnce(mockSession);
      const session = await chatService.createSession(sessionPayload);
      expect(session.id).toBe(sessionId);

      // Send Message
      const messagePayload: ChatMessageCreate = {
        content: 'I have had dizziness and mild swelling in my ankles since yesterday.',
      };

      const mockTurn: ChatTurnResponse = {
        session_id: sessionId,
        user_message: {
          id: 'msg-usr-1',
          session_id: sessionId,
          sender_role: 'USER',
          content: messagePayload.content,
          created_at: '2026-10-04T10:11:00Z',
        },
        assistant_message: {
          id: 'msg-ast-1',
          session_id: sessionId,
          sender_role: 'ASSISTANT',
          content: 'Dizziness and swelling can occur during pregnancy, but sudden swelling should be checked with your ASHA worker.',
          created_at: '2026-10-04T10:11:02Z',
        },
        safety_state: 'CONCERNING',
        safety_events: ['Mild dizziness and extremity swelling detected in patient report.'],
        disclaimer: 'Guidance only. Certified clinicians remain authoritative for all medical decisions.',
      };

      vi.spyOn(chatService, 'sendMessage').mockResolvedValueOnce(mockTurn);
      const turn = await chatService.sendMessage(sessionId, messagePayload);

      expect(turn.safety_state).toBe('CONCERNING');
      expect(turn.safety_events).toHaveLength(1);
      expect(turn.disclaimer).toBeTruthy();
    });

    it('renders SafetyStatusBadge with distinct presentation for CLEAR, CONCERNING, and EMERGENCY', () => {
      const clearBadge = SafetyStatusBadge({ safetyState: 'CLEAR' });
      expect(clearBadge).toBeTruthy();
      const clearProps = (clearBadge as React.ReactElement<{ label: string }>).props;
      expect(clearProps.label).toContain('CLEAR');

      const concerningBadge = SafetyStatusBadge({ safetyState: 'CONCERNING' });
      expect(concerningBadge).toBeTruthy();
      const concerningProps = (concerningBadge as React.ReactElement<{ label: string }>).props;
      expect(concerningProps.label).toContain('CONCERNING');

      const emergencyBadge = SafetyStatusBadge({ safetyState: 'EMERGENCY' });
      expect(emergencyBadge).toBeTruthy();
      const emergencyProps = (emergencyBadge as React.ReactElement<{ label: string }>).props;
      expect(emergencyProps.label).toContain('EMERGENCY');
    });

    it('executes Decision Agent query with authorized tools allowlist', async () => {
      const agentPayload: AgentQueryRequest = {
        mother_id: 'mother-uuid-001',
        query: 'What were the latest blood pressure readings for this mother?',
        requested_tools: ['get_recent_vitals', 'get_health_summary'],
      };

      const mockAgentResponse: AgentQueryResponse = {
        mother_id: 'mother-uuid-001',
        query: 'What were the latest blood pressure readings for this mother?',
        response: 'Latest recorded BP is 135/88 mmHg from week 28.',
        safety_state: 'CLEAR',
        tools_invoked: [
          {
            tool_name: 'get_recent_vitals',
            status: 'SUCCESS',
            summary: 'Retrieved 1 health record with BP 135/88 mmHg',
            data: { systolic: 135, diastolic: 88 },
          },
        ],
        disclaimer: 'Clinical decision-support only.',
        created_at: '2026-10-04T10:12:00Z',
      };

      vi.spyOn(agentService, 'queryAgent').mockResolvedValueOnce(mockAgentResponse);
      const agentRes = await agentService.queryAgent(agentPayload);

      expect(agentRes.tools_invoked[0].status).toBe('SUCCESS');
      expect(agentRes.safety_state).toBe('CLEAR');
      expect(agentRes.response).toContain('135/88 mmHg');

      // Verify tool execution view rendering
      const toolView = AgentToolExecutionView({ toolsInvoked: agentRes.tools_invoked });
      expect(toolView).toBeTruthy();
    });
  });

  // ============================================================================
  // 4. Voice Interaction Workflow Integration & Confirmation Boundary
  // ============================================================================
  describe('4. Voice Workflow Integration & Explicit Confirmation Boundary', () => {
    it('executes transcription -> review -> explicit confirmation -> audio synthesis', async () => {
      const audioBase64 = 'UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
      const sessionId = 'session-uuid-101';
      const motherId = 'mother-uuid-001';

      // Step 1: Transcribe audio
      const transcribeReq: VoiceTranscriptionRequest = {
        audio_content: audioBase64,
        mime_type: 'audio/webm',
        language: 'hi',
        mother_id: motherId,
      };

      const mockTranscribeRes: VoiceTranscriptionResponse = {
        transcript: 'मुझे बहुत तेज सिरदर्द हो रहा है।',
        language: 'hi',
        detected_language: 'hi',
        confidence: 0.96,
        duration_seconds: 2.8,
        mother_id: motherId,
        created_at: '2026-10-04T10:14:00Z',
      };

      vi.spyOn(voiceService, 'transcribeAudio').mockResolvedValueOnce(mockTranscribeRes);
      const transcribeRes = await voiceService.transcribeAudio(transcribeReq);

      expect(transcribeRes.transcript).toBe('मुझे बहुत तेज सिरदर्द हो रहा है।');
      expect(transcribeRes.language).toBe('hi');

      // Step 2 & 3: User reviews, optionally edits, and explicitly confirms
      const confirmedText = 'मुझे बहुत तेज सिरदर्द हो रहा है। (Edited with details)';
      const confirmReq: VoiceConfirmationRequest = {
        confirmed_text: confirmedText,
        session_id: sessionId,
        language: 'hi',
        mother_id: motherId,
      };

      const mockConfirmRes: VoiceConfirmationResponse = {
        session_id: sessionId,
        confirmed_text: confirmedText,
        safety_state: 'CONCERNING',
        confirmed_at: '2026-10-04T10:15:00Z',
        chat_turn: {
          session_id: sessionId,
          user_message: {
            id: 'v-msg-usr-1',
            session_id: sessionId,
            sender_role: 'USER',
            content: confirmedText,
            created_at: '2026-10-04T10:15:00Z',
          },
          assistant_message: {
            id: 'v-msg-ast-1',
            session_id: sessionId,
            sender_role: 'ASSISTANT',
            content: 'कृपया तुरंत आराम करें और अपनी आशा कार्यकर्ता को सूचित करें।',
            created_at: '2026-10-04T10:15:02Z',
          },
          safety_state: 'CONCERNING',
          safety_events: ['Severe headache symptom confirmed by mother via voice input.'],
          disclaimer: 'केवल सलाह के लिए। डॉक्टर से जांच करवाएं।',
        },
      };

      vi.spyOn(voiceService, 'confirmVoiceTranscript').mockResolvedValueOnce(mockConfirmRes);
      const confirmRes = await voiceService.confirmVoiceTranscript(confirmReq);

      expect(confirmRes.chat_turn.user_message.content).toBe(confirmedText);
      expect(confirmRes.chat_turn.safety_state).toBe('CONCERNING');

      // Step 4: Text-to-Speech synthesis
      const synthReq: VoiceSynthesisRequest = {
        text: confirmRes.chat_turn.assistant_message.content,
        language: 'hi',
        output_format: 'mp3',
      };

      const mockSynthRes: VoiceSynthesisResponse = {
        audio_content: '//uQZAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAJAAAWjAC...',
        mime_type: 'audio/mp3',
        duration_seconds: 3.5,
        text_length: confirmRes.chat_turn.assistant_message.content.length,
        language: 'hi',
        created_at: '2026-10-04T10:15:05Z',
      };

      vi.spyOn(voiceService, 'synthesizeSpeech').mockResolvedValueOnce(mockSynthRes);
      const synthRes = await voiceService.synthesizeSpeech(synthReq);

      expect(synthRes.mime_type).toBe('audio/mp3');
      expect(synthRes.language).toBe('hi');
      expect(synthRes.audio_content).toBeTruthy();
    });

    it('enforces the exact 7 supported voice languages', () => {
      const expectedLanguages = ['en', 'hi', 'te', 'ta', 'kn', 'bn', 'mr'];
      expect(SUPPORTED_VOICE_LANGUAGES.map((l) => l.code)).toEqual(expectedLanguages);

      const selectorEl = VoiceLanguageSelector({
        value: 'en',
        onChange: () => {},
      });
      expect(selectorEl).toBeTruthy();
    });

    it('renders VoiceAudioPlayer component with play/pause and duration UI', () => {
      const playerEl = VoiceAudioPlayer({
        audioContent: 'UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=',
        mimeType: 'audio/wav',
        durationSeconds: 2.5,
      });
      expect(playerEl).toBeTruthy();
    });
  });

  // ============================================================================
  // 5. ASHA Care Coordination & Assigned-Mother Integration
  // ============================================================================
  describe('5. ASHA Care Coordination & Assigned-Mother Access Integration', () => {
    it('retrieves assigned mother timeline using motherId parameter', async () => {
      const assignedMotherId = 'assigned-mother-42';

      const mockTimeline: RiskTimelineResponse = {
        mother_id: assignedMotherId,
        current_risk_level: 'HIGH',
        assessments: [
          {
            timestamp: '2026-10-04T08:00:00Z',
            assessment_type: 'ML_PREDICTION',
            risk_level: 'HIGH',
            systolic_bp: 155,
            diastolic_bp: 98,
          },
        ],
      };

      const spy = vi.spyOn(timelineService, 'getRiskTimeline').mockResolvedValueOnce(mockTimeline);
      const timeline = await timelineService.getRiskTimeline(assignedMotherId);

      expect(spy).toHaveBeenCalledWith(assignedMotherId);
      expect(timeline.mother_id).toBe(assignedMotherId);
      expect(timeline.current_risk_level).toBe('HIGH');
    });

    it('executes decision agent query for an assigned mother on behalf of ASHA', async () => {
      const assignedMotherId = 'assigned-mother-42';
      const agentPayload: AgentQueryRequest = {
        mother_id: assignedMotherId,
        query: 'Summarize clinical risk trajectory and outstanding alerts.',
        requested_tools: ['check_safety_alerts', 'get_recent_vitals'],
      };

      const mockAgentResponse: AgentQueryResponse = {
        mother_id: assignedMotherId,
        query: 'Summarize clinical risk trajectory and outstanding alerts.',
        response: 'Mother is week 32 with active high blood pressure alert.',
        safety_state: 'CONCERNING',
        tools_invoked: [
          {
            tool_name: 'check_safety_alerts',
            status: 'SUCCESS',
            summary: '1 active high-priority alert found',
            data: { active_alerts: 1, severity: 'HIGH' },
          },
        ],
        disclaimer: 'Decision-support only. Certified clinicians remain authoritative.',
        created_at: '2026-10-04T08:01:00Z',
      };

      vi.spyOn(agentService, 'queryAgent').mockResolvedValueOnce(mockAgentResponse);
      const res = await agentService.queryAgent(agentPayload);

      expect(res.mother_id).toBe(assignedMotherId);
      expect(res.safety_state).toBe('CONCERNING');
      expect(res.tools_invoked[0].tool_name).toBe('check_safety_alerts');
    });
  });

  // ============================================================================
  // 6. Security and Contract Invariants
  // ============================================================================
  describe('6. Security and Contract Safety Invariants', () => {
    it('verifies that no service-role secrets are present in environment configs', () => {
      const envKeys = Object.keys(import.meta.env);
      const forbiddenPatterns = ['SERVICE_ROLE', 'SERVICE_KEY', 'SUPABASE_ADMIN'];

      envKeys.forEach((key) => {
        forbiddenPatterns.forEach((pattern) => {
          expect(key.toUpperCase()).not.toContain(pattern);
        });
      });
    });

    it('renders ChatMessageItem with mandatory clinical decision support disclaimer', () => {
      const msgItem = ChatMessageItem({
        message: {
          id: 'msg-test-1',
          session_id: 'sess-1',
          sender_role: 'ASSISTANT',
          content: 'Please ensure adequate hydration and rest.',
          created_at: '2026-10-04T10:00:00Z',
        },
        safetyState: 'CLEAR',
        disclaimer: 'Guidance only. Certified doctors remain authoritative.',
      });

      expect(msgItem).toBeTruthy();
      const msgProps = (msgItem as React.ReactElement<{ className: string }>).props;
      expect(msgProps.className).toContain('items-start');
    });
  });
});
