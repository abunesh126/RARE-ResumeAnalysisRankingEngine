import { useState } from 'react';
import { User, Building2, Bell, Palette, Sliders, Save } from 'lucide-react';
import { toast } from 'sonner';

const TABS = [
  { id: 'profile', label: 'Recruiter Profile' },
  { id: 'org', label: 'Organization' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'theme', label: 'Theme' },
  { id: 'preferences', label: 'Preferences' },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState({ name: 'Alex Rivera', role: 'Lead Recruiter', email: 'alex.rivera@nexuscorp.com', phone: '+1 (415) 555-0198', bio: 'Experienced HR professional with 8+ years in tech talent acquisition.' });
  const [org, setOrg] = useState({ name: 'Nexus Corporation', industry: 'Technology', size: '1000-5000', website: 'https://nexuscorp.com', timezone: 'America/Los_Angeles' });
  const [notif, setNotif] = useState({ emailOnComplete: true, inAppAlerts: true, weeklyDigest: false, slackIntegration: false });
  const [theme, setTheme] = useState('light');

  const handleSave = () => toast.success('Settings saved successfully');

  const sectionStyle = { background: 'white', border: '1px solid var(--color-border)', borderRadius: 12, padding: 24, marginBottom: 16 };
  const fieldRow = { display: 'flex', flexDirection: 'column' as const, gap: 4, marginBottom: 16 };
  const label = { fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', letterSpacing: '0.3px' };

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.3px' }}>Settings</h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>Manage your account and application preferences</p>
        </div>
        <button className="btn-primary" onClick={handleSave}><Save size={14} /> Save Changes</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 20 }}>
        {/* Sidebar nav */}
        <div style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: 12, padding: 12, height: 'fit-content' }}>
          {TABS.map((tab) => (
            <button key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                width: '100%', padding: '9px 12px', borderRadius: 8,
                border: 'none', cursor: 'pointer', textAlign: 'left',
                fontSize: 13, fontWeight: activeTab === tab.id ? 600 : 500,
                background: activeTab === tab.id ? 'rgba(101,39,190,0.08)' : 'transparent',
                color: activeTab === tab.id ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                marginBottom: 2, transition: 'all 0.15s',
              }}>
              {tab.id === 'profile' && <User size={14} />}
              {tab.id === 'org' && <Building2 size={14} />}
              {tab.id === 'notifications' && <Bell size={14} />}
              {tab.id === 'theme' && <Palette size={14} />}
              {tab.id === 'preferences' && <Sliders size={14} />}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div>
          {activeTab === 'profile' && (
            <div style={sectionStyle}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>Recruiter Profile</h3>
              {/* Avatar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, padding: 16, background: 'var(--color-surface-2)', borderRadius: 10 }}>
                <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'linear-gradient(135deg, #6527BE, #C2185B)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700, fontSize: 22 }}>AR</div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700 }}>Alex Rivera</div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 8 }}>Lead Recruiter · Nexus Corporation</div>
                  <button className="btn-secondary" style={{ fontSize: 11, padding: '5px 12px' }}>Change Photo</button>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {[
                  { label: 'Full Name', key: 'name', placeholder: 'Your full name' },
                  { label: 'Job Title', key: 'role', placeholder: 'e.g. Lead Recruiter' },
                  { label: 'Email Address', key: 'email', placeholder: 'your@email.com' },
                  { label: 'Phone Number', key: 'phone', placeholder: '+1 (000) 000-0000' },
                ].map(({ label: lbl, key, placeholder }) => (
                  <div key={key} style={fieldRow}>
                    <label style={label}>{lbl}</label>
                    <input className="input-field" value={(profile as any)[key]} onChange={(e) => setProfile((p) => ({ ...p, [key]: e.target.value }))} placeholder={placeholder} />
                  </div>
                ))}
              </div>
              <div style={fieldRow}>
                <label style={label}>Bio</label>
                <textarea className="input-field" value={profile.bio} onChange={(e) => setProfile((p) => ({ ...p, bio: e.target.value }))} style={{ minHeight: 80, resize: 'vertical' }} />
              </div>
            </div>
          )}

          {activeTab === 'org' && (
            <div style={sectionStyle}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>Organization Settings</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {[
                  { label: 'Organization Name', key: 'name' },
                  { label: 'Industry', key: 'industry' },
                  { label: 'Company Size', key: 'size' },
                  { label: 'Website', key: 'website' },
                  { label: 'Timezone', key: 'timezone' },
                ].map(({ label: lbl, key }) => (
                  <div key={key} style={fieldRow}>
                    <label style={label}>{lbl}</label>
                    <input className="input-field" value={(org as any)[key]} onChange={(e) => setOrg((o) => ({ ...o, [key]: e.target.value }))} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div style={sectionStyle}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>Notification Preferences</h3>
              {[
                { key: 'emailOnComplete', label: 'Email on Analysis Complete', desc: 'Get notified via email when an analysis run finishes' },
                { key: 'inAppAlerts', label: 'In-App Alerts', desc: 'Show notifications inside the dashboard' },
                { key: 'weeklyDigest', label: 'Weekly Digest', desc: 'Receive a weekly summary of hiring activity' },
                { key: 'slackIntegration', label: 'Slack Notifications', desc: 'Post updates to your Slack workspace' },
              ].map(({ key, label: lbl, desc }) => (
                <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 0', borderBottom: '1px solid var(--color-border)' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{lbl}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>{desc}</div>
                  </div>
                  <div
                    onClick={() => setNotif((n) => ({ ...n, [key]: !(n as any)[key] }))}
                    style={{
                      width: 44, height: 24, borderRadius: 99, cursor: 'pointer', transition: 'background 0.2s',
                      background: (notif as any)[key] ? 'var(--color-primary)' : '#D8D0EE',
                      position: 'relative', flexShrink: 0,
                    }}>
                    <div style={{
                      width: 18, height: 18, borderRadius: '50%', background: 'white',
                      position: 'absolute', top: 3,
                      left: (notif as any)[key] ? 23 : 3,
                      transition: 'left 0.2s',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                    }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'theme' && (
            <div style={sectionStyle}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>Theme & Appearance</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                {[
                  { id: 'light', label: 'Light', bg: '#F8F6FF', accent: '#6527BE' },
                  { id: 'dark', label: 'Dark', bg: '#1C0A3C', accent: '#C2185B' },
                  { id: 'system', label: 'System', bg: 'linear-gradient(135deg, #F8F6FF 50%, #1C0A3C 50%)', accent: '#6527BE' },
                ].map((t) => (
                  <div key={t.id}
                    onClick={() => setTheme(t.id)}
                    style={{
                      border: `2px solid ${theme === t.id ? 'var(--color-primary)' : 'var(--color-border)'}`,
                      borderRadius: 10, padding: 16, cursor: 'pointer', transition: 'border-color 0.15s',
                    }}>
                    <div style={{ height: 60, borderRadius: 6, background: t.bg, marginBottom: 10, border: '1px solid rgba(0,0,0,0.06)' }} />
                    <div style={{ fontSize: 13, fontWeight: 600, textAlign: 'center' }}>{t.label}</div>
                    {theme === t.id && <div style={{ fontSize: 11, color: 'var(--color-primary)', textAlign: 'center', marginTop: 4 }}>Active</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div style={sectionStyle}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20 }}>Preferences</h3>
              {[
                { label: 'Default Candidates per Analysis', options: ['10', '25', '50', '100'], desc: 'How many candidates to display after each run' },
                { label: 'Default Sort Order', options: ['Score (High to Low)', 'Match % (High to Low)', 'Name (A-Z)', 'Experience (Most)'], desc: 'Default sort when viewing candidate results' },
                { label: 'Score Display', options: ['Percentage', 'Decimal', 'Stars'], desc: 'How to display candidate match scores' },
              ].map((pref, i) => (
                <div key={i} style={{ marginBottom: 20 }}>
                  <label style={{ ...label, display: 'block', marginBottom: 4 }}>{pref.label}</label>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 8 }}>{pref.desc}</div>
                  <select className="input-field" style={{ maxWidth: 300 }}>
                    {pref.options.map((o) => <option key={o}>{o}</option>)}
                  </select>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
