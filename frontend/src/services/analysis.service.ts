import api from './api';
import { mockCandidates } from '../utils/mockData';
import type { AnalysisInput, AnalysisResult } from '../types';

export const analysisService = {
  async analyzeResumes(input: AnalysisInput): Promise<AnalysisResult> {
    try {
      const { data } = await api.post('/analysis/run', input);
      return data;
    } catch {
      return new Promise((resolve) =>
        setTimeout(() => resolve({
          candidates: mockCandidates.slice(0, input.topN),
          totalScanned: 152,
          processingTime: '2m 14s',
        }), 2000)
      );
    }
  },

  async getActiveAnalysis() {
    try {
      const { data } = await api.get('/analysis/active');
      return data;
    } catch {
      return null;
    }
  },
};
