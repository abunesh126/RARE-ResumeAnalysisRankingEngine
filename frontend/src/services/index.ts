import api from './api';
import { mockDashboardStats, mockTemplates, mockHistory, mockBatches } from '../utils/mockData';
import type { JobTemplate, AnalysisHistory, ResumeBatch } from '../types';

export const analyticsService = {
  async getAnalytics() {
    try {
      const { data } = await api.get('/analytics');
      return data;
    } catch {
      return new Promise((resolve) => setTimeout(() => resolve(mockDashboardStats), 700));
    }
  },
};

export const templateService = {
  async getTemplates(): Promise<JobTemplate[]> {
    try {
      const { data } = await api.get('/templates');
      return data;
    } catch {
      return new Promise((resolve) => setTimeout(() => resolve(mockTemplates), 500));
    }
  },

  async createTemplate(template: Omit<JobTemplate, 'id' | 'createdAt'>): Promise<JobTemplate> {
    try {
      const { data } = await api.post('/templates', template);
      return data;
    } catch {
      return { ...template, id: Date.now().toString(), createdAt: new Date().toISOString() };
    }
  },

  async updateTemplate(id: string, template: Partial<JobTemplate>): Promise<JobTemplate> {
    try {
      const { data } = await api.put(`/templates/${id}`, template);
      return data;
    } catch {
      return { ...mockTemplates[0], ...template, id };
    }
  },

  async deleteTemplate(id: string): Promise<void> {
    try {
      await api.delete(`/templates/${id}`);
    } catch {
      return Promise.resolve();
    }
  },
};

export const historyService = {
  async getHistory(): Promise<AnalysisHistory[]> {
    try {
      const { data } = await api.get('/history');
      return data;
    } catch {
      return new Promise((resolve) => setTimeout(() => resolve(mockHistory), 500));
    }
  },
};

export const resumeLibraryService = {
  async getBatches(): Promise<ResumeBatch[]> {
    try {
      const { data } = await api.get('/resume-batches');
      return data;
    } catch {
      return new Promise((resolve) => setTimeout(() => resolve(mockBatches), 600));
    }
  },

  async deleteBatch(id: string): Promise<void> {
    try {
      await api.delete(`/resume-batches/${id}`);
    } catch {
      return Promise.resolve();
    }
  },
};

export const settingsService = {
  async getSettings() {
    try {
      const { data } = await api.get('/settings');
      return data;
    } catch {
      return {
        name: 'Alex Rivera',
        role: 'Lead Recruiter',
        email: 'alex.rivera@company.com',
        organization: 'Nexus Corp',
        notifications: { email: true, inApp: true, weekly: false },
        theme: 'light',
      };
    }
  },

  async updateSettings(settings: Record<string, unknown>): Promise<void> {
    try {
      await api.put('/settings', settings);
    } catch {
      return Promise.resolve();
    }
  },
};
