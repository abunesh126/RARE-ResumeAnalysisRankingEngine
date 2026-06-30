import { useState } from 'react';
import { FileText, Download, BarChart3, Users, Calendar, Building2 } from 'lucide-react';
import { toast } from 'sonner';

const REPORTS = [
  {
    id: 'shortlist',
    icon: <Users size={20} />,
    title: 'Shortlisted Candidate Report',
    description: 'Detailed profiles and scores of all shortlisted candidates from the latest analysis.',
    color: '#6527BE',
    bg: 'rgba(101,39,190,0.08)',
    formats: ['PDF', 'CSV', 'Excel'],
  },
  {
    id: 'analysis',
    icon: <BarChart3 size={20} />,
    title: 'Analysis Report',
    description: 'Full analysis breakdown including skill gaps, score distributions, and AI insights.',
    color: '#2EC4B6',
    bg: 'rgba(46,196,182,0.08)',
    formats: ['PDF', 'CSV'],
  },
  {
    id: 'department',
    icon: <Building2 size={20} />,
    title: 'Department Report',
    description: 'Hiring activity and candidate pipeline breakdown by department and role category.',
    color: '#C2185B',
    bg: 'rgba(194,24,91,0.08)',
    formats: ['PDF', 'Excel'],
  },
  {
    id: 'monthly',
    icon: <Calendar size={20} />,
    title: 'Monthly Hiring Report',
    description: 'Month-over-month trends for sourcing, screening, and conversion metrics.',
    color: '#F2A65A',
    bg: 'rgba(242,166,90,0.1)',
    formats: ['PDF', 'CSV', 'Excel'],
  },
];

export default function ReportsPage() {
  const [generating, setGenerating] = useState<string | null>(null);

  const handleGenerate = (id: string, format: string) => {
    setGenerating(`${id}-${format}`);
    setTimeout(() => {
      setGenerating(null);
      toast.success(`${format} report generated and downloaded`);
    }, 1800);
  };

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Reports</h1>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>Generate and download hiring reports for stakeholder review</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
        {REPORTS.map((report) => (
          <div key={report.id} className="card" style={{ padding: 24 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: report.bg, color: report.color, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
              {report.icon}
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>{report.title}</h3>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6, marginBottom: 20 }}>{report.description}</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {report.formats.map((fmt) => {
                const key = `${report.id}-${fmt}`;
                const isLoading = generating === key;
                return (
                  <button
                    key={fmt}
                    className="btn-secondary"
                    style={{ fontSize: 12, padding: '7px 14px', opacity: isLoading ? 0.7 : 1 }}
                    disabled={!!generating}
                    onClick={() => handleGenerate(report.id, fmt)}
                  >
                    {isLoading ? (
                      <svg width="12" height="12" viewBox="0 0 12 12" style={{ animation: 'spin 1s linear infinite' }}>
                        <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.5" strokeDasharray="22" strokeDashoffset="6" fill="none" />
                      </svg>
                    ) : <Download size={12} />}
                    {fmt}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Recent reports */}
      <div style={{ marginTop: 28 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Recent Reports</h2>
        <div className="card" style={{ overflow: 'hidden' }}>
          {[
            { name: 'Shortlisted Candidates - June 2024', type: 'PDF', date: '2024-06-10', size: '1.2 MB' },
            { name: 'Analysis Report - Q2 Backend Batch', type: 'CSV', date: '2024-06-08', size: '340 KB' },
            { name: 'Monthly Hiring Report - May 2024', type: 'PDF', date: '2024-06-01', size: '2.1 MB' },
            { name: 'Department Breakdown - Engineering', type: 'Excel', date: '2024-05-28', size: '890 KB' },
          ].map((r, i) => (
            <div key={i} className="table-row" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 12 }}>
              <FileText size={16} color="var(--color-primary)" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{r.name}</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>{r.date} · {r.size}</div>
              </div>
              <span style={{ fontSize: 10, fontWeight: 700, background: 'rgba(101,39,190,0.08)', color: 'var(--color-primary)', padding: '2px 8px', borderRadius: 4 }}>{r.type}</span>
              <button className="btn-ghost" style={{ padding: '6px 8px' }} onClick={() => toast.success('Downloading...')}>
                <Download size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
