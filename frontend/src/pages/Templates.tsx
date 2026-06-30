import { useState, useEffect } from 'react';
import { Plus, Search, Edit2, Trash2, Copy, FileText, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { Tag, EmptyState, Modal, Skeleton } from '../components/ui';
import { templateService } from '../services';
import type { JobTemplate } from '../types';

const CATEGORIES = ['All', 'Engineering', 'Infrastructure', 'Data', 'Product', 'Design'];

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<JobTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<JobTemplate | null>(null);
  const [form, setForm] = useState({ title: '', category: 'Engineering', description: '', skills: '' });

  useEffect(() => {
    templateService.getTemplates().then((d) => { setTemplates(d); setLoading(false); });
  }, []);

  const filtered = templates.filter((t) => {
    const matchSearch = t.title.toLowerCase().includes(search.toLowerCase());
    const matchCat = category === 'All' || t.category === category;
    return matchSearch && matchCat;
  });

  const openCreate = () => { setEditing(null); setForm({ title: '', category: 'Engineering', description: '', skills: '' }); setModalOpen(true); };
  const openEdit = (t: JobTemplate) => { setEditing(t); setForm({ title: t.title, category: t.category, description: t.description, skills: t.skills.join(', ') }); setModalOpen(true); };

  const handleSave = async () => {
    const payload = { ...form, skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean) };
    if (editing) {
      await templateService.updateTemplate(editing.id, payload);
      setTemplates((prev) => prev.map((t) => t.id === editing.id ? { ...t, ...payload } : t));
      toast.success('Template updated');
    } else {
      const created = await templateService.createTemplate(payload);
      setTemplates((prev) => [...prev, created]);
      toast.success('Template created');
    }
    setModalOpen(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this template?')) return;
    await templateService.deleteTemplate(id);
    setTemplates((prev) => prev.filter((t) => t.id !== id));
    toast.success('Template deleted');
  };

  const handleDuplicate = async (t: JobTemplate) => {
    const dup = await templateService.createTemplate({ title: `${t.title} (Copy)`, category: t.category, description: t.description, skills: t.skills });
    setTemplates((prev) => [...prev, dup]);
    toast.success('Template duplicated');
  };

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Job Templates</h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>Saved job descriptions for quick analysis setup</p>
        </div>
        <button className="btn-primary" onClick={openCreate}><Plus size={14} /> New Template</button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <div className="search-bar" style={{ flex: 1, maxWidth: 300 }}>
          <Search size={14} color="var(--color-text-muted)" />
          <input placeholder="Search templates..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {CATEGORIES.map((c) => (
            <button key={c} className={`chip${category === c ? ' active' : ''}`} onClick={() => setCategory(c)}>{c}</button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          {Array.from({ length: 4 }, (_, i) => <Skeleton key={i} height={200} />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: 40 }}>
          <EmptyState icon={<FileText size={40} />} title="No templates found" description="Create your first job template to speed up candidate analysis." action={<button className="btn-primary" onClick={openCreate}><Plus size={14} /> Create Template</button>} />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          {filtered.map((t) => (
            <div key={t.id} className="card" style={{ padding: 20, transition: 'box-shadow 0.2s' }}
              onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 4px 16px rgba(101,39,190,0.1)')}
              onMouseLeave={e => (e.currentTarget.style.boxShadow = '')}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 10, fontWeight: 700, background: 'rgba(101,39,190,0.08)', color: 'var(--color-primary)', padding: '3px 8px', borderRadius: 99, letterSpacing: '0.4px' }}>
                  {t.category}
                </span>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button className="btn-ghost" style={{ padding: '4px 6px' }} onClick={() => handleDuplicate(t)}><Copy size={13} /></button>
                  <button className="btn-ghost" style={{ padding: '4px 6px' }} onClick={() => openEdit(t)}><Edit2 size={13} /></button>
                  <button className="btn-ghost" style={{ padding: '4px 6px', color: 'var(--color-danger)' }} onClick={() => handleDelete(t.id)}><Trash2 size={13} /></button>
                </div>
              </div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>{t.title}</h3>
              <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: 12, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                {t.description}
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
                {t.skills.slice(0, 5).map((s) => <Tag key={s}>{s}</Tag>)}
                {t.skills.length > 5 && <Tag>+{t.skills.length - 5}</Tag>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-muted)' }}>
                <Clock size={11} />
                {t.lastUsed ? `Last used ${t.lastUsed}` : `Created ${t.createdAt}`}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Template' : 'New Template'}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>Title</label>
            <input className="input-field" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="e.g. Senior Backend Engineer" />
          </div>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>Category</label>
            <select className="input-field" value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}>
              {CATEGORIES.filter((c) => c !== 'All').map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>Job Description</label>
            <textarea className="input-field" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Full job description..." style={{ minHeight: 120, resize: 'vertical' }} />
          </div>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>Required Skills (comma separated)</label>
            <input className="input-field" value={form.skills} onChange={(e) => setForm((f) => ({ ...f, skills: e.target.value }))} placeholder="Go, Kubernetes, Docker, AWS" />
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button className="btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
            <button className="btn-primary" onClick={handleSave}>{editing ? 'Save Changes' : 'Create Template'}</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
