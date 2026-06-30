import { useState, useEffect } from 'react';
import { TrendingUp, RefreshCw, Eye } from 'lucide-react';
import { Avatar, ScoreCircle, StatusBadge, Skeleton, Tag, EmptyState, Drawer } from '../components/ui';
import { candidateService } from '../services/candidate.service';
import type { Candidate } from '../types';

export default function ActiveRankingsPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Candidate | null>(null);

  useEffect(() => {
    candidateService.getCandidates().then((d) => {
      setCandidates(d.filter((c) => c.score >= 0.6).sort((a, b) => b.score - a.score));
      setLoading(false);
    });
  }, []);

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Active Rankings</h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>Current top-ranked candidates from the latest analysis run</p>
        </div>
        <button className="btn-secondary" style={{ fontSize: 12 }}><RefreshCw size={14} /> Refresh Rankings</button>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', background: 'linear-gradient(135deg, rgba(101,39,190,0.04), rgba(194,24,91,0.03))', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <TrendingUp size={16} color="var(--color-primary)" />
          <span style={{ fontSize: 13, fontWeight: 700 }}>Q2 Backend Engineers · Senior Go Developer Role</span>
          <span className="badge badge-green" style={{ marginLeft: 'auto' }}>LIVE</span>
        </div>

        {loading ? (
          <div style={{ padding: 20 }}>
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid var(--color-border)', alignItems: 'center' }}>
                <Skeleton width={32} height={32} style={{ borderRadius: '50%', flexShrink: 0 }} />
                <Skeleton width={36} height={36} style={{ borderRadius: '50%', flexShrink: 0 }} />
                <div style={{ flex: 1 }}><Skeleton width="60%" height={14} /><Skeleton width="40%" height={11} style={{ marginTop: 4 }} /></div>
                <Skeleton width={52} height={52} style={{ borderRadius: '50%' }} />
              </div>
            ))}
          </div>
        ) : candidates.length === 0 ? (
          <EmptyState icon={<TrendingUp size={40} />} title="No active rankings" description="Run an analysis to see ranked candidates here." />
        ) : candidates.map((c, i) => (
          <div key={c.id} className="table-row" style={{ padding: '14px 20px', display: 'grid', gridTemplateColumns: '32px 2.5fr 1fr 1.5fr 1fr 1fr auto', gap: 12, alignItems: 'center', cursor: 'pointer' }}
            onClick={() => setSelected(c)}>
            {/* Rank */}
            <div style={{
              width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, fontWeight: 800, flexShrink: 0,
              background: i === 0 ? 'linear-gradient(135deg, #FFD700, #FFA500)' : i === 1 ? 'linear-gradient(135deg, #C0C0C0, #A0A0A0)' : i === 2 ? 'linear-gradient(135deg, #CD7F32, #A0522D)' : '#F0ECF8',
              color: i < 3 ? 'white' : 'var(--color-text-muted)',
            }}>#{i + 1}</div>
            {/* Candidate */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Avatar initials={c.initials} color={c.avatarColor} size={36} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{c.name}</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{c.title} · {c.experience}</div>
              </div>
            </div>
            {/* Score */}
            <ScoreCircle score={c.score} />
            {/* Skills */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              {c.skills.slice(0, 2).map((s) => <Tag key={s}>{s}</Tag>)}
              {c.skills.length > 2 && <Tag>+{c.skills.length - 2}</Tag>}
            </div>
            {/* Education */}
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.education.split(',')[0]}</div>
            {/* Status */}
            <StatusBadge status={c.status} />
            {/* Action */}
            <button className="btn-ghost" style={{ padding: '6px 8px' }}><Eye size={14} /></button>
          </div>
        ))}
      </div>

      <Drawer open={!!selected} onClose={() => setSelected(null)} title="Candidate Profile">
        {selected && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <Avatar initials={selected.initials} color={selected.avatarColor} size={52} />
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>{selected.name}</h3>
                <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{selected.title}</p>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Match Score', value: <ScoreCircle score={selected.score} /> },
                { label: 'Experience', value: selected.experience },
                { label: 'Education', value: selected.education.split(',')[0] },
                { label: 'Source', value: selected.source },
              ].map((item) => (
                <div key={item.label} style={{ padding: 14, background: 'var(--color-surface-2)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 6 }}>{item.label}</div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{item.value}</div>
                </div>
              ))}
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 8 }}>SKILLS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {selected.skills.map((s) => <Tag key={s}>{s}</Tag>)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 8 }}>AI INSIGHTS</div>
              <div style={{ padding: 14, background: 'rgba(101,39,190,0.04)', borderRadius: 8, border: '1px solid rgba(101,39,190,0.1)', fontSize: 13, lineHeight: 1.6 }}>
                {selected.insights}
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
