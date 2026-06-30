import type { Candidate, ResumeBatch, JobTemplate, AnalysisHistory, DashboardStats } from '../types';

export const mockCandidates: Candidate[] = [
  {
    id: '1', name: 'Alice Johnson', initials: 'AJ', avatarColor: '#6527BE',
    title: 'Senior Software Engineer', email: 'alice@example.com', location: 'San Francisco, CA',
    score: 0.95, matchPercent: 95, experience: '7 yrs', education: 'M.S. Computer Science, MIT',
    skills: ['Go', 'Docker', 'Kubernetes', 'Microservices', 'gRPC'],
    status: 'shortlisted', source: 'LinkedIn',
    insights: 'Strong match on Cloud Backend Development. Deep expertise in distributed systems.',
  },
  {
    id: '2', name: 'Charlie Davis', initials: 'CD', avatarColor: '#C2185B',
    title: 'Fullstack Developer', email: 'charlie@example.com', location: 'Austin, TX',
    score: 0.72, matchPercent: 72, experience: '4 yrs', education: 'B.S. Computer Science, UT Austin',
    skills: ['Python', 'Django', 'AWS', 'Kubernetes', 'React'],
    status: 'reviewing', source: 'Indeed',
    insights: 'Partial match. Kubernetes experience limited but Python/Django aligns well.',
  },
  {
    id: '3', name: 'Bob Smith', initials: 'BS', avatarColor: '#E84855',
    title: 'Frontend Engineer', email: 'bob@example.com', location: 'New York, NY',
    score: 0.25, matchPercent: 25, experience: '2 yrs', education: 'B.S. Design, NYU',
    skills: ['React', 'CSS', 'HTML', 'TypeScript'],
    status: 'rejected', source: 'Naukri',
    insights: 'No overlap with backend requirements. Frontend only profile.',
  },
  {
    id: '4', name: 'Priya Sharma', initials: 'PS', avatarColor: '#2EC4B6',
    title: 'DevOps Engineer', email: 'priya@example.com', location: 'Bangalore, India',
    score: 0.88, matchPercent: 88, experience: '5 yrs', education: 'B.E. Information Technology, VTU',
    skills: ['Terraform', 'Kubernetes', 'Docker', 'AWS', 'CI/CD', 'Go'],
    status: 'shortlisted', source: 'Campus Drive',
    insights: 'Excellent DevOps background. Strong infra automation skills align perfectly.',
  },
  {
    id: '5', name: 'Marcus Lee', initials: 'ML', avatarColor: '#F2A65A',
    title: 'Backend Engineer', email: 'marcus@example.com', location: 'Seattle, WA',
    score: 0.81, matchPercent: 81, experience: '6 yrs', education: 'M.S. Software Engineering, UW',
    skills: ['Go', 'PostgreSQL', 'Redis', 'gRPC', 'AWS'],
    status: 'shortlisted', source: 'Referral',
    insights: 'Strong Go expertise. Good fit for senior backend roles.',
  },
  {
    id: '6', name: 'Sarah Chen', initials: 'SC', avatarColor: '#AD1457',
    title: 'Cloud Architect', email: 'sarah@example.com', location: 'Chicago, IL',
    score: 0.91, matchPercent: 91, experience: '9 yrs', education: 'M.B.A. + B.S. CS, Stanford',
    skills: ['AWS', 'GCP', 'Terraform', 'Docker', 'Kubernetes', 'Python'],
    status: 'shortlisted', source: 'LinkedIn',
    insights: 'Exceptional cloud architecture background. Multi-cloud certified professional.',
  },
  {
    id: '7', name: 'David Kim', initials: 'DK', avatarColor: '#6527BE',
    title: 'Full Stack Developer', email: 'david@example.com', location: 'Los Angeles, CA',
    score: 0.65, matchPercent: 65, experience: '3 yrs', education: 'B.S. CS, UCLA',
    skills: ['Node.js', 'React', 'MongoDB', 'Docker'],
    status: 'pending', source: 'Career Portal',
    insights: 'Decent full stack experience. Limited cloud exposure.',
  },
  {
    id: '8', name: 'Emma Wilson', initials: 'EW', avatarColor: '#2EC4B6',
    title: 'SRE Engineer', email: 'emma@example.com', location: 'Boston, MA',
    score: 0.85, matchPercent: 85, experience: '5 yrs', education: 'M.S. Systems Engineering, BU',
    skills: ['Kubernetes', 'Prometheus', 'Go', 'Python', 'Terraform'],
    status: 'shortlisted', source: 'Employee Referral',
    insights: 'Strong reliability engineering background. Excellent monitoring expertise.',
  },
];

export const mockBatches: ResumeBatch[] = [
  { id: 'b1', name: 'Q2 Backend Engineers', description: 'Resumes collected from LinkedIn and Indeed for backend roles', resumeCount: 152, createdAt: '2024-05-20', status: 'ready', source: 'LinkedIn + Indeed' },
  { id: 'b2', name: 'Campus Drive IIT 2024', description: 'Fresh graduates from IIT Bombay, Delhi, Madras campus drive', resumeCount: 89, createdAt: '2024-05-15', status: 'analyzed', source: 'Campus Drive' },
  { id: 'b3', name: 'Referral Pool June 2024', description: 'Employee referrals for various open positions', resumeCount: 34, createdAt: '2024-06-01', status: 'ready', source: 'Employee Referrals' },
  { id: 'b4', name: 'Naukri DevOps Batch', description: 'DevOps and Cloud engineers from Naukri portal', resumeCount: 67, createdAt: '2024-05-28', status: 'processing', source: 'Naukri' },
  { id: 'b5', name: 'Frontend Specialist Pool', description: 'React and TypeScript focused frontend engineers', resumeCount: 45, createdAt: '2024-06-05', status: 'ready', source: 'LinkedIn' },
];

export const mockTemplates: JobTemplate[] = [
  { id: 't1', title: 'Senior Backend Engineer', category: 'Engineering', description: 'We are looking for a Senior Backend Engineer with 5+ years experience in Go, Kubernetes, and distributed systems...', skills: ['Go', 'Kubernetes', 'Docker', 'AWS', 'gRPC', 'PostgreSQL'], createdAt: '2024-04-10', lastUsed: '2024-06-01' },
  { id: 't2', title: 'Full Stack Developer', category: 'Engineering', description: 'Full Stack Developer with React on frontend and Node.js/Python on backend...', skills: ['React', 'Node.js', 'Python', 'MongoDB', 'AWS'], createdAt: '2024-03-22', lastUsed: '2024-05-28' },
  { id: 't3', title: 'DevOps Engineer', category: 'Infrastructure', description: 'DevOps Engineer to manage CI/CD pipelines and cloud infrastructure...', skills: ['Terraform', 'AWS', 'Docker', 'Kubernetes', 'Jenkins'], createdAt: '2024-02-15', lastUsed: '2024-05-20' },
  { id: 't4', title: 'Data Scientist', category: 'Data', description: 'Data Scientist with strong ML background and production experience...', skills: ['Python', 'TensorFlow', 'PyTorch', 'SQL', 'Spark'], createdAt: '2024-04-28' },
  { id: 't5', title: 'Product Manager', category: 'Product', description: 'Product Manager with technical background and B2B SaaS experience...', skills: ['Product Strategy', 'SQL', 'Figma', 'JIRA', 'Roadmapping'], createdAt: '2024-05-05' },
];

export const mockHistory: AnalysisHistory[] = [
  { id: 'h1', date: '2024-06-10 14:32', batchName: 'Q2 Backend Engineers', jobDescription: 'Senior Backend Engineer - Go/Kubernetes', candidatesProcessed: 152, averageScore: 0.71, processingTime: '2m 14s', topCandidate: 'Alice Johnson' },
  { id: 'h2', date: '2024-06-08 09:15', batchName: 'Campus Drive IIT 2024', jobDescription: 'Junior Software Engineer - Python', candidatesProcessed: 89, averageScore: 0.63, processingTime: '1m 42s', topCandidate: 'Priya Sharma' },
  { id: 'h3', date: '2024-06-05 16:45', batchName: 'Naukri DevOps Batch', jobDescription: 'DevOps Engineer - Terraform/AWS', candidatesProcessed: 67, averageScore: 0.69, processingTime: '1m 18s', topCandidate: 'Sarah Chen' },
  { id: 'h4', date: '2024-06-01 11:20', batchName: 'Referral Pool June 2024', jobDescription: 'Full Stack Developer - React/Node', candidatesProcessed: 34, averageScore: 0.75, processingTime: '0m 58s', topCandidate: 'David Kim' },
  { id: 'h5', date: '2024-05-28 13:00', batchName: 'Frontend Specialist Pool', jobDescription: 'Senior Frontend Engineer - React/TypeScript', candidatesProcessed: 45, averageScore: 0.68, processingTime: '1m 05s', topCandidate: 'Emma Wilson' },
];

export const mockDashboardStats: DashboardStats = {
  totalCandidates: 152,
  shortlisted: 8,
  averageScore: 0.74,
  processingTime: '2m 14s',
  skillDistribution: [
    { skill: 'Go', count: 45 },
    { skill: 'Kubernetes', count: 58 },
    { skill: 'Docker', count: 72 },
    { skill: 'Python', count: 38 },
    { skill: 'AWS', count: 27 },
    { skill: 'React', count: 19 },
    { skill: 'TypeScript', count: 16 },
    { skill: 'Terraform', count: 12 },
  ],
  scoreDistribution: [
    { range: '90-100%', count: 12, fill: '#2EC4B6' },
    { range: '70-89%', count: 38, fill: '#6527BE' },
    { range: '50-69%', count: 52, fill: '#E8A87C' },
    { range: '30-49%', count: 28, fill: '#F2A65A' },
    { range: '0-29%', count: 22, fill: '#E84855' },
  ],
  experienceDistribution: [
    { range: '0-2 yrs', count: 20 },
    { range: '3-5 yrs', count: 47 },
    { range: '6-8 yrs', count: 34 },
    { range: '9-12 yrs', count: 29 },
    { range: '13+ yrs', count: 16 },
  ],
  hiringFunnel: [
    { stage: 'Total Resumes', count: 152 },
    { stage: 'AI Screened', count: 120 },
    { stage: 'Score > 50%', count: 78 },
    { stage: 'Score > 70%', count: 32 },
    { stage: 'Shortlisted', count: 8 },
  ],
  monthliyTrend: [
    { month: 'Jan', candidates: 45, shortlisted: 5 },
    { month: 'Feb', candidates: 62, shortlisted: 7 },
    { month: 'Mar', candidates: 38, shortlisted: 4 },
    { month: 'Apr', candidates: 91, shortlisted: 10 },
    { month: 'May', candidates: 128, shortlisted: 14 },
    { month: 'Jun', candidates: 152, shortlisted: 8 },
  ],
  sourceDistribution: [
    { name: 'LinkedIn', value: 42 },
    { name: 'Naukri', value: 24 },
    { name: 'Indeed', value: 16 },
    { name: 'Referral', value: 10 },
    { name: 'Campus', value: 5 },
    { name: 'Portal', value: 3 },
  ],
};
