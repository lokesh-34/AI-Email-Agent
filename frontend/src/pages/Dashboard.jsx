import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboard, getNotifications, processEmails } from '../api/api';
import Toast from '../components/Toast';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [statsData, notifsData] = await Promise.all([
        getDashboard(),
        getNotifications(),
      ]);
      setStats(statsData);
      setNotifications(notifsData.slice(0, 8));
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleProcess() {
    setProcessing(true);
    try {
      const result = await processEmails(10);
      setToast({
        message: `Processed ${result.processed} emails. Tasks: ${result.tasks_created}, Events: ${result.events_created}, Drafts: ${result.drafts_created}`,
        type: 'success',
      });
      loadData();
    } catch (err) {
      setToast({ message: err.message, type: 'error' });
    } finally {
      setProcessing(false);
    }
  }

  function handleNotifClick(notif) {
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

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Loading dashboard...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Dashboard</h2>
          <p>Your AI email command center</p>
        </div>
        <button
          className={`btn btn-primary process-btn ${processing ? 'processing' : ''}`}
          onClick={handleProcess}
          disabled={processing}
        >
          {processing ? '⏳ Processing...' : '🔄 Process Emails'}
        </button>
      </div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card" onClick={() => navigate('/tasks')}>
            <div className="stat-icon">📋</div>
            <div className="stat-value">{stats.pending_tasks}</div>
            <div className="stat-label">Pending Tasks</div>
          </div>
          <div className="stat-card" onClick={() => navigate('/tasks')}>
            <div className="stat-icon">🔥</div>
            <div className="stat-value">{stats.high_priority}</div>
            <div className="stat-label">High Priority</div>
          </div>
          <div className="stat-card" onClick={() => navigate('/calendar')}>
            <div className="stat-icon">📅</div>
            <div className="stat-value">{stats.upcoming_events}</div>
            <div className="stat-label">Upcoming Events</div>
          </div>
          <div className="stat-card" onClick={() => navigate('/drafts')}>
            <div className="stat-icon">✉️</div>
            <div className="stat-value">{stats.draft_replies}</div>
            <div className="stat-label">Draft Replies</div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>🔔 Recent Notifications</h3>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/notifications')}>
            View All
          </button>
        </div>
        {notifications.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>All clear!</h3>
            <p>No notifications right now. Process emails to get started.</p>
          </div>
        ) : (
          <div className="card-list">
            {notifications.map((notif) => (
              <div
                key={notif.id}
                className="item-card"
                onClick={() => handleNotifClick(notif)}
              >
                <div className="item-header">
                  <span className="item-title">
                    {priorityIcon(notif.priority)} {notif.title}
                  </span>
                  <span className={`badge badge-${notif.priority}`}>
                    {notif.priority}
                  </span>
                </div>
                {notif.description && (
                  <div className="item-description">{notif.description}</div>
                )}
                <div className="item-meta">
                  {notif.category && (
                    <span className="badge badge-category">{notif.category}</span>
                  )}
                  {notif.date && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {notif.date}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
