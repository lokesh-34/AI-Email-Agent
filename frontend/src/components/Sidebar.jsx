import { NavLink } from 'react-router-dom';

export default function Sidebar({ user, onLogout }) {
  const links = [
    { to: '/', icon: '📊', label: 'Dashboard' },
    { to: '/notifications', icon: '🔔', label: 'Notifications' },
    { to: '/tasks', icon: '✅', label: 'Tasks' },
    { to: '/drafts', icon: '✉️', label: 'Drafts' },
    { to: '/calendar', icon: '📅', label: 'Calendar' },
    { to: '/assistant', icon: '🤖', label: 'AI Assistant' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>AI Email Copilot</h1>
        <span>Intelligent Assistant</span>
      </div>

      <nav className="sidebar-nav">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <span className="nav-icon">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {/* User Info */}
        {user && (
          <div className="sidebar-user">
            {user.picture ? (
              <img
                src={user.picture}
                alt={user.name || user.email}
                className="sidebar-user-avatar"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="sidebar-user-avatar sidebar-user-avatar-placeholder">
                {(user.name || user.email || '?')[0].toUpperCase()}
              </div>
            )}
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">
                {user.name || 'User'}
              </div>
              <div className="sidebar-user-email">
                {user.email}
              </div>
            </div>
          </div>
        )}

        {/* Sign Out */}
        {onLogout && (
          <button
            className="sidebar-logout-btn"
            onClick={onLogout}
            title="Sign out"
          >
            <span>🚪</span> Sign Out
          </button>
        )}

        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          Powered by Groq AI
        </div>
      </div>
    </aside>
  );
}
