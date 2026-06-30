import api from './api';
import { mockDashboardStats } from '../utils/mockData';
import type { DashboardStats } from '../types';

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    try {
      const { data } = await api.get('/dashboard');
      return data;
    } catch {
      // Return mock data when backend unavailable
      return new Promise((resolve) => setTimeout(() => resolve(mockDashboardStats), 800));
    }
  },
};
