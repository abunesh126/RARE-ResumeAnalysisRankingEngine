import { useState, useEffect } from 'react';
import { Download, Share2, Info, Users, CheckCircle, TrendingUp, Clock, FolderOpen, HardDrive } from 'lucide-react';
import { toast } from 'sonner';
import { Skeleton } from '../components/ui';
import { analysisService } from '../services/analysis.service';
import { dashboardService } from '../services/dashboard.service';
import { mockCandidates } from '../utils/mockData';
import type { Candidate, DashboardStats } from '../types';
import { useNavigate } from 'react-router-dom';

// Precise score circle matching the reference
function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  let bg = '#1A56DB';
  let color = 'white';
  if (pct >= 85) { bg = '#059669'; }
  else if (pct >= 55) { bg = '#D1D5DB'; color = '#374151'; }
  else { bg = '#FCA5A5'; color = '#991B1B'; }
  return (
    <div style={{
      width: 54, height: 54, borderRadius: '50%',
      background: bg, color,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontWeight: 800, fontSize: 15,
      flexShrink: 0,
    }}>
      {score.toFixed(2)}
    </div>
  );
}

function SkillTag({ label }: { label: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px',
      background: '#EFF6FF', color: '#1D4ED8',
      borderRadius: 4, fontSize: 11, fontWeight: 500,
      marginRight: 3, marginBottom: 3,
    }}>
      {label}
    </span>
  );
}

// Candidate avatar circle
function CandidateAvatar({ initials, bg }: { initials: string; bg: string }) {
  return (
    <div style={{
      width: 40, height: 40, borderRadius: '50%',
      background: bg, color: 'white',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontWeight: 700, fontSize: 13, flexShrink: 0,
    }}>
      {initials}
    </div>
  );
}

export default function DashboardPage() {
  const [jobDesc, setJobDesc] = useState('');
  const [topN, setTopN] = useState(3);
  const [loading, setLoading] = useState(false);
  const [_analysed, setAnalysed] = useState(false);
  const [results, setResults] = useState<Candidate[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const navigate = useNavigate();

  // Pre-load sample results to match reference image
  useEffect(() => {
    dashboardService.getStats().then((s) => { setStats(s); setStatsLoading(false); });
    // Show sample candidates like in the screenshot
    setTimeout(() => {
      setResults(mockCandidates.slice(0, 3));
      setAnalysed(true);
    }, 400);
  }, []);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const result = await analysisService.analyzeResumes({ batchId: 'b1', jobDescription: jobDesc, topN });
      setResults(result.candidates.slice(0, topN));
      setAnalysed(true);
      toast.success(`Analysis complete — ${result.candidates.length} candidates ranked`);
    } catch {
      toast.error('Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const kpis = [
    { icon: <Users size={18} />, label: 'Total Candidates', value: stats?.totalCandidates ?? 0, color: '#6366F1', bg: '#EEF2FF', change: '+12%' },
    { icon: <CheckCircle size={18} />, label: 'Shortlisted', value: stats?.shortlisted ?? 0, color: '#059669', bg: '#ECFDF5', change: '+3 today' },
    { icon: <TrendingUp size={18} />, label: 'Avg Match Score', value: stats ? `${Math.round((stats.averageScore ?? 0) * 100)}%` : '—', color: '#DC2626', bg: '#FEF2F2', change: '↑ 4%' },
    { icon: <Clock size={18} />, label: 'Processing Time', value: stats?.processingTime ?? '—', color: '#D97706', bg: '#FFFBEB', change: 'Last run' },
  ];

  return (
    <div style={{ animation: 'pageEnter 0.25s ease forwards' }}>
      {/* Page header */}
      <div style={{ marginBottom: 22 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#111827', letterSpacing: '-0.5px', lineHeight: 1.2 }}>Analysis Dashboard</h1>
        <p style={{ fontSize: 14, color: '#6B7280', marginTop: 5 }}>Review candidate rankings and AI-driven skill gap analysis.</p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 22 }}>
        {kpis.map((kpi, i) => (
          <div key={i} style={{
            background: 'white', border: '1px solid #E5E7EB',
            borderRadius: 12, padding: '16px 18px',
            display: 'flex', alignItems: 'center', gap: 14,
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: kpi.bg, color: kpi.color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {kpi.icon}
            </div>
            {statsLoading ? (
              <div><Skeleton width={50} height={20} /><Skeleton width={90} height={12} style={{ marginTop: 4 }} /></div>
            ) : (
              <div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#111827', lineHeight: 1.2 }}>{kpi.value}</div>
                <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>{kpi.label}</div>
                <div style={{ fontSize: 11, color: kpi.color, marginTop: 2, fontWeight: 500 }}>{kpi.change}</div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Main 2-col */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.05fr', gap: 18 }}>

        {/* ── LEFT: Analysis Input ── */}
        <div style={{
          background: 'white', border: '1px solid #E5E7EB',
          borderRadius: 14, padding: '22px 22px 18px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          display: 'flex', flexDirection: 'column', gap: 0,
        }}>
          {/* Card header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
              <div style={{ width: 30, height: 30, borderRadius: 8, background: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                  <circle cx="7.5" cy="7.5" r="6" stroke="#6366F1" strokeWidth="1.5"/>
                  <path d="M5 7.5L7 9.5L10 6" stroke="#6366F1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Analysis Input</span>
            </div>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.6px',
              color: '#059669', background: '#ECFDF5',
              border: '1px solid #A7F3D0',
              padding: '3px 10px', borderRadius: 99,
            }}>ACTIVE BATCH</span>
          </div>

          {/* Upload Resumes section */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#1A56DB', marginBottom: 10, letterSpacing: '0.1px' }}>Upload Resumes</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {/* Folder Upload */}
              <div style={{
                border: '1.5px dashed #D1D5DB', borderRadius: 10,
                padding: '18px 12px', display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 8,
                cursor: 'pointer', transition: 'all 0.15s', background: '#FAFAFA',
              }}
                onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = '#1A56DB'; (e.currentTarget as HTMLDivElement).style.background = '#F0F5FF'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = '#D1D5DB'; (e.currentTarget as HTMLDivElement).style.background = '#FAFAFA'; }}>
                <FolderOpen size={26} color="#9CA3AF" />
                <span style={{ fontSize: 12, color: '#6B7280', fontWeight: 500 }}>Folder Upload</span>
              </div>
              {/* Google Drive */}
              <div style={{
                border: '1.5px dashed #D1D5DB', borderRadius: 10,
                padding: '18px 12px', display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 8,
                cursor: 'pointer', transition: 'all 0.15s', background: '#FAFAFA',
              }}
                onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = '#1A56DB'; (e.currentTarget as HTMLDivElement).style.background = '#F0F5FF'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = '#D1D5DB'; (e.currentTarget as HTMLDivElement).style.background = '#FAFAFA'; }}>
                <HardDrive size={26} color="#9CA3AF" />
                <span style={{ fontSize: 12, color: '#6B7280', fontWeight: 500 }}>Google Drive</span>
              </div>
            </div>
          </div>

          {/* Job Requirements & Description */}
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 8 }}>Job Requirements & Description</div>
            <textarea
              value={jobDesc}
              onChange={e => setJobDesc(e.target.value)}
              placeholder="Paste the full job description here. Include tech stack, years of experience, and key responsibilities..."
              style={{
                width: '100%', minHeight: 138,
                border: '1px solid #D1D5DB', borderRadius: 8,
                padding: '10px 12px', fontSize: 13, color: '#374151',
                outline: 'none', resize: 'vertical', fontFamily: 'inherit',
                lineHeight: 1.5, background: 'white',
                transition: 'border-color 0.15s',
                boxSizing: 'border-box',
              }}
              onFocus={e => e.target.style.borderColor = '#1A56DB'}
              onBlur={e => e.target.style.borderColor = '#D1D5DB'}
            />
          </div>

          {/* Slider */}
          <div style={{ marginBottom: 18 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Top Candidates to Display</span>
              <div style={{
                width: 26, height: 26, borderRadius: '50%',
                background: '#1A56DB', color: 'white',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, flexShrink: 0,
              }}>{topN}</div>
            </div>
            <input
              type="range" min={1} max={50} value={topN}
              onChange={e => setTopN(Number(e.target.value))}
              style={{
                width: '100%', height: 4, cursor: 'pointer',
                appearance: 'none', borderRadius: 99, outline: 'none',
                background: `linear-gradient(to right, #1A56DB ${(topN / 50) * 100}%, #E5E7EB ${(topN / 50) * 100}%)`,
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#9CA3AF', marginTop: 5, fontWeight: 600, letterSpacing: '0.5px' }}>
              <span>FOCUS</span>
              <span>BROAD REVIEW</span>
            </div>
          </div>

          {/* Analyze Button */}
          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              width: '100%', padding: '14px',
              background: loading ? '#6B7280' : '#1A56DB',
              color: 'white', border: 'none', borderRadius: 9,
              fontSize: 14, fontWeight: 800, letterSpacing: '1px',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: '0 2px 8px rgba(26,86,219,0.35)',
              transition: 'all 0.15s',
            }}
          >
            {loading ? (
              <>
                <svg width="15" height="15" viewBox="0 0 15 15" style={{ animation: 'spin 1s linear infinite' }}>
                  <circle cx="7.5" cy="7.5" r="6" stroke="white" strokeWidth="2" strokeDasharray="25" strokeDashoffset="7" fill="none"/>
                </svg>
                ANALYSING...
              </>
            ) : (
              <>
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                  <path d="M7.5 2L9.5 6.5L14 7.5L10.5 11L11.5 15.5L7.5 13L3.5 15.5L4.5 11L1 7.5L5.5 6.5L7.5 2Z" fill="white"/>
                </svg>
                ANALYSE CANDIDATES
              </>
            )}
          </button>
        </div>

        {/* ── RIGHT: Final Ranked Shortlist ── */}
        <div style={{
          background: 'white', border: '1px solid #E5E7EB',
          borderRadius: 14, overflow: 'hidden',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          display: 'flex', flexDirection: 'column',
        }}>
          {/* Header */}
          <div style={{
            padding: '18px 22px', borderBottom: '1px solid #F3F4F6',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M7 1L8.5 5H13L9.5 7.5L11 12L7 9.5L3 12L4.5 7.5L1 5H5.5L7 1Z" fill="#6366F1"/>
                </svg>
              </div>
              <span style={{ fontSize: 14, fontWeight: 800, color: '#111827', letterSpacing: '0.3px' }}>FINAL RANKED SHORTLIST</span>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button style={{ width: 32, height: 32, borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Download size={15} color="#6B7280" />
              </button>
              <button style={{ width: 32, height: 32, borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Share2 size={15} color="#6B7280" />
              </button>
            </div>
          </div>

          {/* Column headers */}
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 0.9fr 1.6fr 1.8fr',
            padding: '9px 22px',
            background: '#F9FAFB', borderBottom: '1px solid #F3F4F6',
          }}>
            {['CANDIDATE', 'SCORE', 'TOP SKILLS', 'INSIGHTS'].map(h => (
              <div key={h} style={{ fontSize: 10, fontWeight: 700, color: '#9CA3AF', letterSpacing: '0.7px' }}>{h}</div>
            ))}
          </div>

          {/* Candidate rows */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {loading ? (
              [0,1,2].map(i => (
                <div key={i} style={{ padding: '18px 22px', borderBottom: '1px solid #F3F4F6', display: 'flex', gap: 12, alignItems: 'center' }}>
                  <Skeleton width={40} height={40} style={{ borderRadius: '50%' }} />
                  <div style={{ flex: 1 }}>
                    <Skeleton width={110} height={14} />
                    <Skeleton width={80} height={11} style={{ marginTop: 5 }} />
                  </div>
                  <Skeleton width={54} height={54} style={{ borderRadius: '50%' }} />
                </div>
              ))
            ) : results.length === 0 ? (
              <div style={{ padding: '60px 20px', textAlign: 'center', color: '#9CA3AF' }}>
                <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.4 }}>🎯</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#6B7280' }}>No analysis run yet</div>
                <div style={{ fontSize: 12, marginTop: 5 }}>Select a batch and click Analyse Candidates</div>
              </div>
            ) : results.map((c, idx) => (
              <div key={c.id} style={{
                display: 'grid', gridTemplateColumns: '2fr 0.9fr 1.6fr 1.8fr',
                padding: '16px 22px', alignItems: 'center',
                borderBottom: idx < results.length - 1 ? '1px solid #F3F4F6' : 'none',
                cursor: 'pointer',
                transition: 'background 0.1s',
              }}
                onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.background = '#F9FAFB'}
                onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.background = 'white'}
              >
                {/* Candidate */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                  <CandidateAvatar initials={c.initials} bg={c.avatarColor} />
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{c.name}</div>
                    <div style={{ fontSize: 12, color: '#9CA3AF', marginTop: 1 }}>{c.title}</div>
                  </div>
                </div>

                {/* Score */}
                <div>
                  <ScoreBadge score={c.score} />
                  {/* Progress bar under score */}
                  <div style={{ width: 54, height: 3, borderRadius: 99, background: '#F3F4F6', marginTop: 5, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', borderRadius: 99,
                      background: c.score >= 0.85 ? '#059669' : c.score >= 0.55 ? '#6366F1' : '#EF4444',
                      width: `${c.score * 100}%`,
                    }} />
                  </div>
                </div>

                {/* Skills */}
                <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                  {c.skills.slice(0, 4).map(s => <SkillTag key={s} label={s} />)}
                </div>

                {/* Insights */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                  <Info size={13} color="#6366F1" style={{ flexShrink: 0, marginTop: 1 }} />
                  <p style={{ fontSize: 11.5, color: '#6B7280', lineHeight: 1.5, margin: 0 }}>
                    "{c.insights.slice(0, 65)}..."
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div style={{
            padding: '13px 22px', borderTop: '1px solid #F3F4F6',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: '#F9FAFB',
          }}>
            <span style={{ fontSize: 12, color: '#6B7280' }}>
              Showing top {results.length} of 152 scanned resumes
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                style={{
                  padding: '8px 16px', borderRadius: 8,
                  border: '1px solid #E5E7EB', background: 'white',
                  fontSize: 12.5, fontWeight: 600, color: '#374151', cursor: 'pointer',
                }}
                onClick={() => navigate('/candidates')}
              >
                View All Candidates
              </button>
              <button
                style={{
                  padding: '8px 16px', borderRadius: 8,
                  background: '#1A56DB', border: 'none',
                  fontSize: 12.5, fontWeight: 600, color: 'white', cursor: 'pointer',
                  boxShadow: '0 1px 4px rgba(26,86,219,0.3)',
                }}
                onClick={() => { setResults([]); setAnalysed(false); }}
              >
                Refine Search
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pro Tip banner */}
      <div style={{
        marginTop: 18, padding: '13px 18px',
        background: '#EFF6FF', border: '1px solid #BFDBFE',
        borderRadius: 10, display: 'flex', gap: 10, alignItems: 'flex-start',
      }}>
        <Info size={15} color="#1D4ED8" style={{ flexShrink: 0, marginTop: 1 }} />
        <p style={{ fontSize: 13, color: '#1E40AF', lineHeight: 1.5, margin: 0 }}>
          <strong>Pro Tip:</strong> Higher score thresholds ensure better cultural and technical alignment for niche roles like Senior Cloud Engineers.
        </p>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pageEnter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        input[type='range']::-webkit-slider-thumb {
          -webkit-appearance: none; width: 18px; height: 18px;
          border-radius: 50%; background: #1A56DB;
          cursor: pointer; border: 3px solid white;
          box-shadow: 0 1px 4px rgba(26,86,219,0.4);
        }
        input[type='range'] { -webkit-appearance: none; appearance: none; }
      `}</style>
    </div>
  );
}
