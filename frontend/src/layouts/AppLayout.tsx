import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, Library, FileText, History,
  Settings, HelpCircle, LogOut, Bell, Search,
  Plus, HelpCircle as HelpIcon,
} from 'lucide-react';
import { Toaster } from 'sonner';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/rankings', icon: TrendingUp, label: 'Active Rankings' },
  { to: '/library', icon: Library, label: 'Resume Library' },
  { to: '/templates', icon: FileText, label: 'Job Templates' },
  { to: '/history', icon: History, label: 'History' },
];

export default function AppLayout() {
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <div style={{ minHeight: '100vh', background: '#E8EBF0', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}>
      {/* App window container */}
      <div style={{
        width: '100%', minHeight: '100vh',
        background: '#F0F2F7',
        display: 'flex', flexDirection: 'row',
        overflow: 'hidden',
      }}>
        {/* Sidebar */}
        <aside style={{
          width: 220, minHeight: '100vh',
          background: '#FFFFFF',
          borderRight: '1px solid #E4E8EF',
          display: 'flex', flexDirection: 'column',
          flexShrink: 0,
          zIndex: 50,
        }}>
          {/* Logo */}
          <div style={{ padding: '20px 18px 16px', borderBottom: '1px solid #EEF0F5' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: '#1A56DB',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 2L14 5V11L8 14L2 11V5L8 2Z" fill="white" opacity="0.9"/>
                  <path d="M8 5L11 6.5V9.5L8 11L5 9.5V6.5L8 5Z" fill="white"/>
                </svg>
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#1A56DB', letterSpacing: '-0.3px' }}>
                Nexus Resume Ranker
              </div>
            </div>
          </div>

          {/* Nav Items */}
          <nav style={{ flex: 1, padding: '12px 10px', display: 'flex', flexDirection: 'column' }}>
            {navItems.map(({ to, icon: Icon, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                style={({ isActive }) => ({
                  display: 'flex', alignItems: 'center', gap: 9,
                  padding: '9px 12px', borderRadius: 7,
                  color: isActive ? '#1A56DB' : '#6B7280',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: 13.5,
                  textDecoration: 'none',
                  background: isActive ? '#EBF2FF' : 'transparent',
                  marginBottom: 2,
                  transition: 'all 0.15s',
                })}
              >
                {({ isActive }) => (
                  <>
                    <Icon size={15} color={isActive ? '#1A56DB' : '#9CA3AF'} />
                    {label}
                  </>
                )}
              </NavLink>
            ))}

            {/* New Analysis Button */}
            <div style={{ marginTop: 16 }}>
              <NavLink to="/" style={{ textDecoration: 'none' }}>
                <button style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
                  width: '100%', padding: '10px 16px',
                  background: '#1A56DB', color: 'white',
                  border: 'none', borderRadius: 8, cursor: 'pointer',
                  fontSize: 13.5, fontWeight: 600,
                  boxShadow: '0 2px 8px rgba(26,86,219,0.35)',
                  transition: 'all 0.15s',
                }}>
                  <Plus size={15} />
                  New Analysis
                </button>
              </NavLink>
            </div>
          </nav>

          {/* Bottom nav */}
          <div style={{ padding: '10px 10px 16px', borderTop: '1px solid #EEF0F5' }}>
            <NavLink to="/support" style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 9,
              padding: '9px 12px', borderRadius: 7,
              color: isActive ? '#1A56DB' : '#6B7280',
              fontWeight: 500, fontSize: 13.5, textDecoration: 'none',
              background: isActive ? '#EBF2FF' : 'transparent', marginBottom: 2,
            })}>
              <HelpCircle size={15} color="#9CA3AF" /> Support
            </NavLink>
            <button style={{
              display: 'flex', alignItems: 'center', gap: 9,
              padding: '9px 12px', borderRadius: 7,
              color: '#6B7280', fontWeight: 500, fontSize: 13.5,
              background: 'transparent', border: 'none', cursor: 'pointer', width: '100%',
            }}>
              <LogOut size={15} color="#9CA3AF" /> Sign Out
            </button>
          </div>
        </aside>

        {/* Main area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          {/* Header */}
          <header style={{
            height: 58, background: '#FFFFFF',
            borderBottom: '1px solid #E4E8EF',
            display: 'flex', alignItems: 'center',
            padding: '0 24px', gap: 4,
            flexShrink: 0, zIndex: 40,
          }}>
            {/* Nav tabs */}
            <NavLink to="/" end style={{ textDecoration: 'none' }}>
              {({ isActive }) => (
                <div style={{
                  padding: '4px 14px', fontSize: 14, fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#1A56DB' : '#6B7280',
                  borderBottom: isActive ? '2px solid #1A56DB' : '2px solid transparent',
                  height: 58, display: 'flex', alignItems: 'center', cursor: 'pointer',
                }}>
                  Dashboard
                </div>
              )}
            </NavLink>
            <NavLink to="/candidates" style={{ textDecoration: 'none' }}>
              {({ isActive }) => (
                <div style={{
                  padding: '4px 14px', fontSize: 14, fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#1A56DB' : '#6B7280',
                  borderBottom: isActive ? '2px solid #1A56DB' : '2px solid transparent',
                  height: 58, display: 'flex', alignItems: 'center', cursor: 'pointer',
                }}>
                  Candidates
                </div>
              )}
            </NavLink>
            <NavLink to="/analytics" style={{ textDecoration: 'none' }}>
              {({ isActive }) => (
                <div style={{
                  padding: '4px 14px', fontSize: 14, fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#1A56DB' : '#6B7280',
                  borderBottom: isActive ? '2px solid #1A56DB' : '2px solid transparent',
                  height: 58, display: 'flex', alignItems: 'center', cursor: 'pointer',
                }}>
                  Analytics
                </div>
              )}
            </NavLink>

            {/* Search */}
            <div style={{ marginLeft: 'auto', flex: '0 0 auto', maxWidth: 260 }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: '#F9FAFB', border: '1px solid #E4E8EF',
                borderRadius: 20, padding: '7px 14px',
              }}>
                <Search size={14} color="#9CA3AF" />
                <input
                  placeholder="Search profiles..."
                  style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, color: '#374151', width: 160 }}
                />
              </div>
            </div>

            {/* Right icons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 12 }}>
              <button style={{ position: 'relative', width: 34, height: 34, borderRadius: '50%', background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                onClick={() => setNotifOpen(!notifOpen)}>
                <Bell size={18} color="#6B7280" />
                <span style={{
                  position: 'absolute', top: 5, right: 5,
                  width: 8, height: 8, borderRadius: '50%',
                  background: '#EF4444', border: '2px solid white',
                }} />
              </button>
              <button style={{ width: 34, height: 34, borderRadius: '50%', background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Settings size={18} color="#6B7280" />
              </button>
              <button style={{ width: 34, height: 34, borderRadius: '50%', background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <HelpIcon size={18} color="#6B7280" />
              </button>

              {/* Profile */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 8, borderLeft: '1px solid #E4E8EF', cursor: 'pointer' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', lineHeight: 1.2 }}>Alex Rivera</div>
                  <div style={{ fontSize: 10, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Lead Recruiter</div>
                </div>
                <div style={{
                  width: 34, height: 34, borderRadius: '50%',
                  background: '#374151',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  overflow: 'hidden', flexShrink: 0,
                }}>
                  <img src="https://i.pravatar.cc/34?img=12" alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                </div>
              </div>
            </div>

            {/* Notification dropdown */}
            {notifOpen && (
              <div style={{
                position: 'absolute', right: 24, top: 58,
                width: 300, background: 'white', borderRadius: 10,
                border: '1px solid #E4E8EF',
                boxShadow: '0 8px 32px rgba(0,0,0,0.12)', zIndex: 100, overflow: 'hidden',
              }}>
                <div style={{ padding: '14px 16px', borderBottom: '1px solid #F3F4F6', fontWeight: 600, fontSize: 13 }}>Notifications</div>
                {[
                  { title: 'Analysis complete', msg: 'Q2 Backend batch processed', time: '2m ago', color: '#10B981' },
                  { title: 'New resume batch ready', msg: 'Campus Drive IIT 2024', time: '1h ago', color: '#1A56DB' },
                  { title: 'Export ready', msg: 'Shortlist CSV downloaded', time: '3h ago', color: '#F59E0B' },
                ].map((n, i) => (
                  <div key={i} style={{ padding: '12px 16px', borderBottom: '1px solid #F9FAFB', display: 'flex', gap: 10, cursor: 'pointer' }}>
                    <div style={{ width: 7, height: 7, borderRadius: '50%', background: n.color, marginTop: 4, flexShrink: 0 }} />
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600 }}>{n.title}</div>
                      <div style={{ fontSize: 11, color: '#9CA3AF' }}>{n.msg} · {n.time}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </header>

          {/* Page content */}
          <main style={{ flex: 1, padding: '28px 28px', minHeight: 0, background: '#F0F2F7' }}>
            <Outlet />
          </main>
        </div>
      </div>

      <Toaster position="top-right" richColors />
    </div>
  );
}
