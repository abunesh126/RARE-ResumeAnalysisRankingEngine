export interface Candidate {
  id: string;
  name: string;
  initials: string;
  avatarColor: string;
  title: string;
  email: string;
  location: string;
  score: number;
  matchPercent: number;
  experience: string;
  education: string;
  skills: string[];
  status: 'shortlisted' | 'reviewing' | 'rejected' | 'pending';
  source: string;
  insights: string;
  resumeUrl?: string;
}

export interface ResumeBatch {
  id: string;
  name: string;
  description: string;
  resumeCount: number;
  createdAt: string;
  status: 'ready' | 'processing' | 'analyzed';
  source: string;
}

export interface JobTemplate {
  id: string;
  title: string;
  category: string;
  description: string;
  skills: string[];
  createdAt: string;
  lastUsed?: string;
}

export interface AnalysisHistory {
  id: string;
  date: string;
  batchName: string;
  jobDescription: string;
  candidatesProcessed: number;
  averageScore: number;
  processingTime: string;
  topCandidate: string;
}

export interface DashboardStats {
  totalCandidates: number;
  shortlisted: number;
  averageScore: number;
  processingTime: string;
  skillDistribution: { skill: string; count: number }[];
  scoreDistribution: { range: string; count: number; fill: string }[];
  experienceDistribution: { range: string; count: number }[];
  hiringFunnel: { stage: string; count: number }[];
  monthliyTrend: { month: string; candidates: number; shortlisted: number }[];
  sourceDistribution: { name: string; value: number }[];
}

export interface AnalysisInput {
  batchId: string;
  jobDescription: string;
  templateId?: string;
  topN: number;
}

export interface AnalysisResult {
  candidates: Candidate[];
  totalScanned: number;
  processingTime: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning';
  title: string;
  message: string;
  time: string;
  read: boolean;
}
