/**
 * ML Prediction API service.
 * Handles triggering ML risk assessments.
 * Contract: POST /api/v1/predictions
 * 
 * Safety Notice: model_score is an internal screening metric, NOT a calibrated
 * clinical probability. Frontend must not present model_score as diagnostic certainty.
 */

import { apiRequest } from './apiClient';
import type { PredictionRequest, PredictionResponse } from '../types/mother';

export const predictionService = {
  /**
   * Request ML risk evaluation for a health record or feature input.
   * Calls POST /api/v1/predictions with Bearer token.
   */
  async requestPrediction(
    payload: PredictionRequest,
    token?: string | null
  ): Promise<PredictionResponse> {
    return apiRequest<PredictionResponse>('/predictions', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
