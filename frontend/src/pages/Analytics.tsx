import { useState, useEffect } from 'react';
import { Download } from 'lucide-react';
import { Skeleton } from '../components/ui';
import {
  SkillBarChart, ScoreDonutChart, ExperienceBarChart,
  MonthlyTrendChart, SourcePieChart, HiringFunnelChart,
} from '../components/charts';
import { analyticsService } from '../services';
import type { DashboardStats } from '../types';

export default function AnalyticsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('30d');

  useEffect(() => {
    analyticsService.getAnalytics().then((d) => {
      setStats(d);
      setLoading(false);
    });
  }, []);

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Reports & Analytics</h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>Comprehensive hiring intelligence and talent insights</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <select className="input-field" style={{ width: 'auto' }} value={dateRange} onChange={(e) => setDateRange(e.target.value)}>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="all">All time</option>
          </select>
          <button className="btn-secondary" style={{ fontSize: 12 }}>
            <Download size={14} /> Export Report
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} height={300} />
          ))}
        </div>
      ) : stats ? (
        <>
          {/* Row 1 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20, marginBottom: 20 }}>
            <SkillBarChart data={stats.skillDistribution} />
            <ScoreDonutChart data={stats.scoreDistribution} />
            <ExperienceBarChart data={stats.experienceDistribution} />
          </div>

          {/* Row 2 */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 20 }}>
            <MonthlyTrendChart data={stats.monthliyTrend} />
            <SourcePieChart data={stats.sourceDistribution} />
          </div>

          {/* Row 3 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <HiringFunnelChart data={stats.hiringFunnel} />
            {/* Top KPIs summary */}
            <div style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Key Metrics Summary</div>
              {[
                { label: 'Offer Acceptance Rate', value: '78%', delta: '+5%', positive: true },
                { label: 'Time to Hire (avg)', value: '18 days', delta: '-3d', positive: true },
                { label: 'Cost per Hire', value: '$3,200', delta: '-12%', positive: true },
                { label: 'Candidate Quality Score', value: '74%', delta: '+8%', positive: true },
                { label: 'Sourcing Efficiency', value: '4.2x', delta: '+0.6x', positive: true },
                { label: 'Pipeline Velocity', value: '11 days', delta: '-2d', positive: true },
              ].map((m, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: i < 5 ? '1px solid var(--color-border)' : 'none' }}>
                  <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{m.label}</span>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700 }}>{m.value}</span>
                    <span style={{ fontSize: 11, color: m.positive ? 'var(--color-success)' : 'var(--color-danger)', background: m.positive ? 'rgba(46,196,182,0.1)' : 'rgba(232,72,85,0.1)', padding: '2px 6px', borderRadius: 99 }}>
                      {m.delta}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
