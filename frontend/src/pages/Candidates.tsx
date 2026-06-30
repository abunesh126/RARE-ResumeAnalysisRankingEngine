import { useState, useEffect } from 'react';
import { Search, Download, ChevronUp, ChevronDown, Eye, X } from 'lucide-react';
import { toast } from 'sonner';
import { Avatar, ScoreCircle, StatusBadge, Skeleton, Tag, Drawer, Pagination, EmptyState } from '../components/ui';
import { candidateService } from '../services/candidate.service';
import type { Candidate } from '../types';

const STATUS_OPTIONS = ['all', 'shortlisted', 'reviewing', 'pending', 'rejected'];

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState<'score' | 'name' | 'matchPercent'>('score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [selected, setSelected] = useState<string[]>([]);
  const [drawerCandidate, setDrawerCandidate] = useState<Candidate | null>(null);
  const [page, setPage] = useState(1);
  const PER_PAGE = 6;

  useEffect(() => {
    candidateService.getCandidates().then((data) => {
      setCandidates(data);
      setLoading(false);
    });
  }, []);

  const filtered = candidates
    .filter((c) => {
      const matchSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        c.skills.some((s) => s.toLowerCase().includes(search.toLowerCase()));
      const matchStatus = statusFilter === 'all' || c.status === statusFilter;
      return matchSearch && matchStatus;
    })
    .sort((a, b) => {
      const mul = sortDir === 'desc' ? -1 : 1;
      if (sortField === 'name') return mul * a.name.localeCompare(b.name);
      return mul * (a[sortField] - b[sortField]);
    });

  const paginated = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) setSortDir(sortDir === 'desc' ? 'asc' : 'desc');
    else { setSortField(field); setSortDir('desc'); }
  };

  const handleExport = async () => {
    const blob = await candidateService.exportCsv(selected.length ? selected : undefined);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'candidates.csv'; a.click();
    toast.success('Candidates exported');
  };

  const toggleSelect = (id: string) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);

  const SortIcon = ({ field }: { field: typeof sortField }) =>
    sortField === field
      ? (sortDir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />)
      : <ChevronDown size={12} style={{ opacity: 0.3 }} />;

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Candidates</h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>
            {loading ? '…' : `${filtered.length} candidates`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {selected.length > 0 && (
            <button className="btn-secondary" style={{ fontSize: 12 }}>
              {selected.length} selected <X size={12} onClick={() => setSelected([])} />
            </button>
          )}
          <button className="btn-secondary" style={{ fontSize: 12 }} onClick={handleExport}>
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        {/* Toolbar */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="search-bar" style={{ flex: '1', minWidth: 220 }}>
            <Search size={14} color="var(--color-text-muted)" />
            <input placeholder="Search candidates, skills..." value={search} onChange={(e) => setSearch(e.target.value)} />
            {search && <X size={14} color="var(--color-text-muted)" style={{ cursor: 'pointer', flexShrink: 0 }} onClick={() => setSearch('')} />}
          </div>

          <div style={{ display: 'flex', gap: 6 }}>
            {STATUS_OPTIONS.map((s) => (
              <button key={s} className={`chip${statusFilter === s ? ' active' : ''}`} onClick={() => setStatusFilter(s)}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--color-surface-2)' }}>
                <th style={{ padding: '10px 20px', textAlign: 'left', width: 40 }}>
                  <input type="checkbox" onChange={(e) => setSelected(e.target.checked ? candidates.map((c) => c.id) : [])}
                    checked={selected.length === candidates.length && candidates.length > 0} />
                </th>
                {[
                  { label: 'Name', field: 'name' as const },
                  { label: 'Match %', field: 'matchPercent' as const },
                  { label: 'Score', field: 'score' as const },
                  { label: 'Skills', field: null },
                  { label: 'Education', field: null },
                  { label: 'Experience', field: null },
                  { label: 'Status', field: null },
                  { label: 'Location', field: null },
                  { label: '', field: null },
                ].map(({ label, field }) => (
                  <th key={label} style={{ padding: '10px 12px', textAlign: 'left', fontSize: 10, fontWeight: 700, color: 'var(--color-text-muted)', letterSpacing: '0.6px', whiteSpace: 'nowrap', cursor: field ? 'pointer' : 'default' }}
                    onClick={() => field && handleSort(field)}
                  >
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      {label}{field && <SortIcon field={field} />}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }, (_, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    {Array.from({ length: 9 }, (_, j) => (
                      <td key={j} style={{ padding: '14px 12px' }}><Skeleton width="80%" height={14} /></td>
                    ))}
                  </tr>
                ))
              ) : paginated.length === 0 ? (
                <tr><td colSpan={9}><EmptyState title="No candidates found" description="Try adjusting your search or filters" /></td></tr>
              ) : paginated.map((c) => (
                <tr key={c.id} className="table-row" style={{ cursor: 'pointer' }} onClick={() => setDrawerCandidate(c)}>
                  <td style={{ padding: '14px 20px' }} onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={selected.includes(c.id)} onChange={() => toggleSelect(c.id)} />
                  </td>
                  <td style={{ padding: '14px 12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <Avatar initials={c.initials} color={c.avatarColor} size={34} />
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600 }}>{c.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{c.title}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '14px 12px' }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: c.matchPercent >= 80 ? 'var(--color-success)' : c.matchPercent >= 50 ? 'var(--color-primary)' : 'var(--color-danger)' }}>
                      {c.matchPercent}%
                    </div>
                    <div style={{ height: 3, width: 48, borderRadius: 99, background: '#EDE8F5', overflow: 'hidden', marginTop: 4 }}>
                      <div style={{ height: '100%', borderRadius: 99, background: c.matchPercent >= 80 ? 'var(--color-success)' : 'var(--color-primary)', width: `${c.matchPercent}%` }} />
                    </div>
                  </td>
                  <td style={{ padding: '14px 12px' }}><ScoreCircle score={c.score} /></td>
                  <td style={{ padding: '14px 12px' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      {c.skills.slice(0, 3).map((s) => <Tag key={s}>{s}</Tag>)}
                      {c.skills.length > 3 && <Tag>+{c.skills.length - 3}</Tag>}
                    </div>
                  </td>
                  <td style={{ padding: '14px 12px', fontSize: 12, color: 'var(--color-text-secondary)', maxWidth: 160 }}>{c.education}</td>
                  <td style={{ padding: '14px 12px', fontSize: 12, color: 'var(--color-text-secondary)' }}>{c.experience}</td>
                  <td style={{ padding: '14px 12px' }}><StatusBadge status={c.status} /></td>
                  <td style={{ padding: '14px 12px', fontSize: 12, color: 'var(--color-text-muted)' }}>{c.location}</td>
                  <td style={{ padding: '14px 12px' }}>
                    <button className="btn-ghost" style={{ padding: '6px 8px' }} onClick={(e) => { e.stopPropagation(); setDrawerCandidate(c); }}>
                      <Eye size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filtered.length > PER_PAGE && (
          <div style={{ padding: '12px 20px', borderTop: '1px solid var(--color-border)' }}>
            <Pagination page={page} total={filtered.length} perPage={PER_PAGE} onChange={setPage} />
          </div>
        )}
      </div>

      {/* Candidate Drawer */}
      <Drawer open={!!drawerCandidate} onClose={() => setDrawerCandidate(null)} title="Candidate Details">
        {drawerCandidate && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <Avatar initials={drawerCandidate.initials} color={drawerCandidate.avatarColor} size={52} />
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>{drawerCandidate.name}</h3>
                <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{drawerCandidate.title}</p>
                <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{drawerCandidate.location}</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Match Score', value: <ScoreCircle score={drawerCandidate.score} /> },
                { label: 'Match %', value: `${drawerCandidate.matchPercent}%` },
                { label: 'Experience', value: drawerCandidate.experience },
                { label: 'Source', value: drawerCandidate.source },
              ].map((item) => (
                <div key={item.label} style={{ padding: 14, background: 'var(--color-surface-2)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 6 }}>{item.label}</div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{item.value}</div>
                </div>
              ))}
            </div>

            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 8 }}>EDUCATION</div>
              <p style={{ fontSize: 13 }}>{drawerCandidate.education}</p>
            </div>

            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 8 }}>SKILLS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {drawerCandidate.skills.map((s) => <Tag key={s}>{s}</Tag>)}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 8 }}>AI INSIGHTS</div>
              <div style={{ padding: 14, background: 'rgba(101,39,190,0.04)', borderRadius: 8, border: '1px solid rgba(101,39,190,0.1)', fontSize: 13, lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
                {drawerCandidate.insights}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}
                onClick={() => { candidateService.updateStatus(drawerCandidate.id, 'shortlisted'); toast.success('Candidate shortlisted'); setDrawerCandidate(null); }}>
                ✓ Shortlist
              </button>
              <button className="btn-secondary" style={{ flex: 1, justifyContent: 'center' }}
                onClick={() => { candidateService.updateStatus(drawerCandidate.id, 'rejected'); toast.error('Candidate rejected'); setDrawerCandidate(null); }}>
                ✗ Reject
              </button>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
