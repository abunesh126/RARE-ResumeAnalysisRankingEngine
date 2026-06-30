import { useState, useEffect } from 'react';
import { Search, Library, RefreshCw, Trash2, ExternalLink, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { StatusBadge, Skeleton, EmptyState } from '../components/ui';
import { resumeLibraryService } from '../services';
import type { ResumeBatch } from '../types';
import { useNavigate } from 'react-router-dom';

export default function ResumeLibraryPage() {
  const [batches, setBatches] = useState<ResumeBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    resumeLibraryService.getBatches().then((d) => {
      setBatches(d);
      setLoading(false);
    });
  }, []);

  const filtered = batches.filter((b) =>
    b.name.toLowerCase().includes(search.toLowerCase()) ||
    b.source.toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    await resumeLibraryService.deleteBatch(id);
    setBatches((prev) => prev.filter((b) => b.id !== id));
    toast.success('Batch deleted');
  };

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Resume Library</h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>All resume batches collected from your sourcing channels</p>
        </div>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
          <div className="search-bar">
            <Search size={14} color="var(--color-text-muted)" />
            <input placeholder="Search batches by name or source..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Array.from({ length: 4 }, (_, i) => <Skeleton key={i} height={80} />)}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState icon={<Library size={40} />} title="No resume batches" description="Resume batches from your sourcing channels will appear here." />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--color-surface-2)' }}>
                {['Batch Name', 'Source', 'Resumes', 'Created', 'Status', 'Actions'].map((h) => (
                  <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 10, fontWeight: 700, color: 'var(--color-text-muted)', letterSpacing: '0.6px' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((batch) => (
                <tr key={batch.id} className="table-row">
                  <td style={{ padding: '16px 20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(101,39,190,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <FileText size={16} color="var(--color-primary)" />
                      </div>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600 }}>{batch.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', maxWidth: 260 }}>{batch.description}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '16px 20px', fontSize: 12, color: 'var(--color-text-secondary)' }}>{batch.source}</td>
                  <td style={{ padding: '16px 20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-primary)' }}>{batch.resumeCount}</span>
                      <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>resumes</span>
                    </div>
                  </td>
                  <td style={{ padding: '16px 20px', fontSize: 12, color: 'var(--color-text-secondary)' }}>{batch.createdAt}</td>
                  <td style={{ padding: '16px 20px' }}><StatusBadge status={batch.status} /></td>
                  <td style={{ padding: '16px 20px' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn-primary" style={{ fontSize: 11, padding: '6px 12px' }} onClick={() => navigate('/')}>
                        <ExternalLink size={12} /> Analyse
                      </button>
                      <button className="btn-secondary" style={{ fontSize: 11, padding: '6px 12px' }}>
                        <RefreshCw size={12} /> Re-run
                      </button>
                      <button className="btn-ghost" style={{ padding: '6px 8px', color: 'var(--color-danger)' }}
                        onClick={() => handleDelete(batch.id, batch.name)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
