import { HelpCircle, MessageCircle, FileText, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';

export default function SupportPage() {
  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Support</h1>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>Get help with RARE — Resume Analysis & Ranking Engine</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20, marginBottom: 28 }}>
        {[
          { icon: <FileText size={22} />, title: 'Documentation', desc: 'Browse guides and API references', color: '#6527BE', bg: 'rgba(101,39,190,0.08)', action: 'Open Docs' },
          { icon: <MessageCircle size={22} />, title: 'Contact Support', desc: 'Reach out to our HR tech support team', color: '#2EC4B6', bg: 'rgba(46,196,182,0.08)', action: 'Start Chat' },
          { icon: <HelpCircle size={22} />, title: 'FAQ', desc: 'Answers to the most common questions', color: '#C2185B', bg: 'rgba(194,24,91,0.08)', action: 'View FAQ' },
        ].map((card) => (
          <div key={card.title} className="card" style={{ padding: 24, textAlign: 'center' }}>
            <div style={{ width: 56, height: 56, borderRadius: 14, background: card.bg, color: card.color, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' }}>{card.icon}</div>
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 6 }}>{card.title}</h3>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 16 }}>{card.desc}</p>
            <button className="btn-secondary" style={{ fontSize: 12 }} onClick={() => toast.info(`Opening ${card.title}...`)}>
              <ExternalLink size={12} /> {card.action}
            </button>
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: 24 }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Send a Message</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 560 }}>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>Subject</label>
            <input className="input-field" placeholder="Briefly describe your issue" />
          </div>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>Category</label>
            <select className="input-field">
              <option>Technical Issue</option>
              <option>Billing</option>
              <option>Feature Request</option>
              <option>Data / Privacy</option>
              <option>Other</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 6 }}>Message</label>
            <textarea className="input-field" placeholder="Describe your issue in detail..." style={{ minHeight: 120, resize: 'vertical' }} />
          </div>
          <div>
            <button className="btn-primary" onClick={() => toast.success('Support ticket submitted! We\'ll respond within 24 hours.')}>Submit Ticket</button>
          </div>
        </div>
      </div>
    </div>
  );
}
