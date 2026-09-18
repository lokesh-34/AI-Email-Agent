import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getNotifications } from '../api/api';

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadNotifications();
  }, []);

  async function loadNotifications() {
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  }

  function handleClick(notif) {
    if (notif.type === 'draft' && notif.draft_id) {
      navigate('/drafts');
    } else if (notif.message_id) {
      navigate(`/email/${notif.message_id}`);
    }
  }

  const priorityIcon = (p) => {
    if (p === 'high') return '🔴';
    if (p === 'medium') return '🟡';
    return '🔵';
  };

  const typeLabel = (t) => {
    const labels = {
      task: '📋 Task',
      reply: '✉️ Reply Needed',
      event: '📅 Event',
      deadline: '⏰ Deadline',
      draft: '📝 Draft',
    };
    return labels[t] || t;
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Loading notifications...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h2>Notifications</h2>
        <p>Items that need your attention</p>
      </div>

      {notifications.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔔</div>
          <h3>No notifications</h3>
          <p>Process some emails to see what needs your attention.</p>
        </div>
      ) : (
        <div className="card-list">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className="item-card"
              onClick={() => handleClick(notif)}
            >
              <div className="item-header">
                <span className="item-title">
                  {priorityIcon(notif.priority)} {notif.title}
                </span>
                <div className="btn-group">
                  <span className={`badge badge-${notif.priority}`}>
                    {notif.priority}
                  </span>
                </div>
              </div>
              {notif.description && (
                <div className="item-description">{notif.description}</div>
              )}
              <div className="item-meta">
                <span className="badge badge-category">{typeLabel(notif.type)}</span>
                {notif.category && (
                  <span className="badge badge-category">{notif.category}</span>
                )}
                {notif.date && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {notif.date}
                  </span>
                )}
                {notif.action && (
                  <span style={{ fontSize: '0.78rem', color: 'var(--accent-primary-light)' }}>
                    → {notif.action}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
