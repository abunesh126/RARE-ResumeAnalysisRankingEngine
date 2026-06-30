import React from 'react';
import { clsx } from 'clsx';
import type { ReactNode, ButtonHTMLAttributes, InputHTMLAttributes, TextareaHTMLAttributes } from 'react';

// Button
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ variant = 'primary', size = 'md', loading, icon, children, className, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        variant === 'primary' && 'btn-primary',
        variant === 'secondary' && 'btn-secondary',
        variant === 'ghost' && 'btn-ghost',
        variant === 'danger' && 'btn-primary',
        size === 'sm' && '!py-1.5 !px-3 !text-xs',
        size === 'lg' && '!py-3 !px-6 !text-sm',
        variant === 'danger' && '!bg-red-500 hover:!bg-red-600',
        className
      )}
      disabled={disabled || loading}
      style={{ opacity: disabled || loading ? 0.7 : 1, cursor: disabled || loading ? 'not-allowed' : 'pointer' }}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="2" strokeDasharray="30" strokeDashoffset="10" />
        </svg>
      ) : icon}
      {children}
    </button>
  );
}

// Card
export function Card({ children, className, ...props }: { children: ReactNode; className?: string; [key: string]: unknown }) {
  return (
    <div className={clsx('card', className)} {...props}>
      {children}
    </div>
  );
}

// Input
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: ReactNode;
}

export function Input({ label, error, icon, className, ...props }: InputProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {label && <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', letterSpacing: '0.3px' }}>{label}</label>}
      <div style={{ position: 'relative' }}>
        {icon && <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }}>{icon}</span>}
        <input className={clsx('input-field', icon && 'pl-8', className)} style={icon ? { paddingLeft: 32 } : {}} {...props} />
      </div>
      {error && <span style={{ fontSize: 11, color: 'var(--color-danger)' }}>{error}</span>}
    </div>
  );
}

// Textarea
interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}
export function Textarea({ label, error, className, ...props }: TextareaProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {label && <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', letterSpacing: '0.3px' }}>{label}</label>}
      <textarea className={clsx('input-field', className)} style={{ resize: 'vertical', minHeight: 120 }} {...props} />
      {error && <span style={{ fontSize: 11, color: 'var(--color-danger)' }}>{error}</span>}
    </div>
  );
}

// Select
export function Select({ label, children, className, ...props }: { label?: string; children: ReactNode; className?: string; [key: string]: unknown }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {label && <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', letterSpacing: '0.3px' }}>{label}</label>}
      <select className={clsx('input-field', className)} {...props}>
        {children}
      </select>
    </div>
  );
}

// Badge
export function Badge({ variant = 'purple', children }: { variant?: 'purple' | 'green' | 'red' | 'amber' | 'gray' | 'blue'; children: ReactNode }) {
  return <span className={clsx('badge', `badge-${variant}`)}>{children}</span>;
}

// Skeleton
export function Skeleton({ width, height, className, style }: { width?: string | number; height?: string | number; className?: string; style?: React.CSSProperties }) {
  return <div className={clsx('skeleton', className)} style={{ width, height: height || 16, ...style }} />;
}

// Avatar
export function Avatar({ name, initials, color, size = 38 }: { name?: string; initials: string; color?: string; size?: number }) {
  const colors = ['#6527BE', '#C2185B', '#2EC4B6', '#F2A65A', '#AD1457', '#E84855'];
  const bg = color || colors[Math.abs((name || initials).charCodeAt(0)) % colors.length];
  return (
    <div
      style={{
        width: size, height: size, borderRadius: '50%',
        background: bg + '22', color: bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 700, fontSize: size * 0.35,
        flexShrink: 0, border: `1.5px solid ${bg}33`,
      }}
    >
      {initials}
    </div>
  );
}

// Score circle
export function ScoreCircle({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? 'var(--color-success)' : pct >= 50 ? 'var(--color-primary)' : 'var(--color-danger)';
  const bg = pct >= 80 ? 'rgba(46,196,182,0.12)' : pct >= 50 ? 'rgba(101,39,190,0.12)' : 'rgba(232,72,85,0.1)';
  return (
    <div style={{
      background: bg, color, fontWeight: 700, fontSize: 15,
      width: 52, height: 52, borderRadius: '50%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      border: `2px solid ${color}33`,
    }}>
      {pct}
    </div>
  );
}

// Status badge
export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; variant: 'green' | 'amber' | 'red' | 'gray' | 'purple' | 'blue' }> = {
    shortlisted: { label: 'Shortlisted', variant: 'green' },
    reviewing: { label: 'Reviewing', variant: 'amber' },
    rejected: { label: 'Rejected', variant: 'red' },
    pending: { label: 'Pending', variant: 'gray' },
    ready: { label: 'Ready', variant: 'green' },
    processing: { label: 'Processing', variant: 'amber' },
    analyzed: { label: 'Analyzed', variant: 'purple' },
  };
  const { label, variant } = map[status] || { label: status, variant: 'gray' as const };
  return <Badge variant={variant}>{label}</Badge>;
}

// Pagination
export function Pagination({ page, total, perPage, onChange }: { page: number; total: number; perPage: number; onChange: (p: number) => void }) {
  const pages = Math.ceil(total / perPage);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center', paddingTop: 16 }}>
      <button className="btn-ghost" style={{ padding: '6px 10px' }} onClick={() => onChange(page - 1)} disabled={page === 1}>‹</button>
      {Array.from({ length: Math.min(pages, 5) }, (_, i) => {
        const p = i + 1;
        return (
          <button key={p} onClick={() => onChange(p)}
            style={{
              width: 32, height: 32, borderRadius: 6, fontSize: 13, fontWeight: 500,
              border: '1px solid', cursor: 'pointer', transition: 'all 0.15s',
              background: p === page ? 'var(--color-primary)' : 'transparent',
              color: p === page ? 'white' : 'var(--color-text-secondary)',
              borderColor: p === page ? 'var(--color-primary)' : 'var(--color-border)',
            }}
          >{p}</button>
        );
      })}
      <button className="btn-ghost" style={{ padding: '6px 10px' }} onClick={() => onChange(page + 1)} disabled={page === pages}>›</button>
    </div>
  );
}

// Modal
export function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>{title}</h3>
          <button onClick={onClose} className="btn-ghost" style={{ padding: '4px 8px', fontSize: 18, lineHeight: 1 }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// Empty State
export function EmptyState({ icon, title, description, action }: { icon?: ReactNode; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      {icon && <div style={{ marginBottom: 16, color: 'var(--color-text-muted)', opacity: 0.5 }}>{icon}</div>}
      <h4 style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 6 }}>{title}</h4>
      {description && <p style={{ fontSize: 13, color: 'var(--color-text-muted)', maxWidth: 320, lineHeight: 1.5 }}>{description}</p>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}

// Drawer
export function Drawer({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  if (!open) return null;
  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid var(--color-border)' }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>{title}</h3>
          <button onClick={onClose} className="btn-ghost" style={{ padding: '4px 8px', fontSize: 18 }}>×</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>{children}</div>
      </div>
    </>
  );
}

// Tag
export function Tag({ children }: { children: ReactNode }) {
  return <span className="tag">{children}</span>;
}

// Tabs
export function Tabs({ tabs, active, onChange }: { tabs: { id: string; label: string }[]; active: string; onChange: (id: string) => void }) {
  return (
    <div className="tab-bar">
      {tabs.map((tab) => (
        <button key={tab.id} className={clsx('tab-item', active === tab.id && 'active')} onClick={() => onChange(tab.id)}>
          {tab.label}
        </button>
      ))}
    </div>
  );
}
