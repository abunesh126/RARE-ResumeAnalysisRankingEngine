import api from './api';
import { mockCandidates } from '../utils/mockData';
import type { Candidate } from '../types';

export const candidateService = {
  async getCandidates(): Promise<Candidate[]> {
    try {
      const { data } = await api.get('/candidates');
      return data;
    } catch {
      return new Promise((resolve) => setTimeout(() => resolve(mockCandidates), 600));
    }
  },

  async getCandidate(id: string): Promise<Candidate> {
    try {
      const { data } = await api.get(`/candidates/${id}`);
      return data;
    } catch {
      return new Promise((resolve) =>
        setTimeout(() => resolve(mockCandidates.find((c) => c.id === id) || mockCandidates[0]), 400)
      );
    }
  },

  async updateStatus(id: string, status: Candidate['status']): Promise<void> {
    try {
      await api.patch(`/candidates/${id}`, { status });
    } catch {
      return Promise.resolve();
    }
  },

  async exportCsv(ids?: string[]): Promise<Blob> {
    try {
      const { data } = await api.post('/candidates/export/csv', { ids }, { responseType: 'blob' });
      return data;
    } catch {
      const csv = 'Name,Score,Match%,Skills,Status\n' + mockCandidates.map((c) =>
        `"${c.name}",${c.score},${c.matchPercent},"${c.skills.join(', ')}",${c.status}`
      ).join('\n');
      return new Blob([csv], { type: 'text/csv' });
    }
  },
};
