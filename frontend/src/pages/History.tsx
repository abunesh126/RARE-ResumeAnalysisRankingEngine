import { useState, useEffect } from 'react';
import { Download, RefreshCw, Clock, Users, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { Skeleton, EmptyState } from '../components/ui';
import { historyService } from '../services';
import type { AnalysisHistory } from '../types';

export default function HistoryPage() {
  const [history, setHistory] = useState<AnalysisHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    historyService.getHistory().then((d) => { setHistory(d); setLoading(false); });
  }, []);

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Analysis History</h1>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>All past analysis runs and their results</p>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--color-surface-2)' }}>
              {['Date', 'Batch', 'Job Description', 'Processed', 'Avg Score', 'Time', 'Top Candidate', 'Actions'].map((h) => (
                <th key={h} style={{ padding: '10px 18px', textAlign: 'left', fontSize: 10, fontWeight: 700, color: 'var(--color-text-muted)', letterSpacing: '0.6px', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }, (_, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  {Array.from({ length: 8 }, (_, j) => (
                    <td key={j} style={{ padding: '14px 18px' }}><Skeleton width="80%" height={14} /></td>
                  ))}
                </tr>
              ))
            ) : history.length === 0 ? (
              <tr><td colSpan={8}><EmptyState icon={<Clock size={40} />} title="No history yet" description="Your analysis runs will appear here." /></td></tr>
            ) : history.map((h) => (
              <tr key={h.id} className="table-row">
                <td style={{ padding: '14px 18px', fontSize: 12, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap' }}>{h.date}</td>
                <td style={{ padding: '14px 18px', fontSize: 13, fontWeight: 600, maxWidth: 160 }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h.batchName}</div>
                </td>
                <td style={{ padding: '14px 18px', fontSize: 12, color: 'var(--color-text-secondary)', maxWidth: 200 }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h.jobDescription}</div>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <Users size={12} color="var(--color-text-muted)" />
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{h.candidatesProcessed}</span>
                  </div>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <TrendingUp size={12} color="var(--color-success)" />
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-primary)' }}>{Math.round(h.averageScore * 100)}%</span>
                  </div>
                </td>
                <td style={{ padding: '14px 18px', fontSize: 12, color: 'var(--color-text-secondary)' }}>{h.processingTime}</td>
                <td style={{ padding: '14px 18px', fontSize: 12, fontWeight: 600 }}>{h.topCandidate}</td>
                <td style={{ padding: '14px 18px' }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn-secondary" style={{ fontSize: 11, padding: '5px 10px' }} onClick={() => toast.success('Report downloaded')}>
                      <Download size={12} /> Report
                    </button>
                    <button className="btn-ghost" style={{ fontSize: 11, padding: '5px 8px' }} onClick={() => toast.info('Re-running analysis...')}>
                      <RefreshCw size={12} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
