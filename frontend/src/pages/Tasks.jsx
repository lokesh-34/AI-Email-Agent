import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTasks, completeTask } from '../api/api';
import Toast from '../components/Toast';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadTasks();
  }, [filter]);

  async function loadTasks() {
    setLoading(true);
    try {
      const data = await getTasks(filter === 'all' ? null : filter);
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleComplete(messageId, e) {
    e.stopPropagation();
    try {
      await completeTask(messageId);
      setToast({ message: 'Task marked as completed!', type: 'success' });
      loadTasks();
    } catch (err) {
      setToast({ message: err.message, type: 'error' });
    }
  }

  const priorityIcon = (p) => {
    if (p === 'high') return '🔴';
    if (p === 'medium') return '🟡';
    return '🟢';
  };

  return (
    <div>
      <div className="page-header">
        <h2>Tasks</h2>
        <p>Email-extracted actions and to-dos</p>
      </div>

      <div className="filter-tabs">
        {['pending', 'completed', 'all'].map((f) => (
          <button
            key={f}
            className={`filter-tab ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">
          <div className="loading-spinner" />
          Loading tasks...
        </div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✅</div>
          <h3>No {filter} tasks</h3>
          <p>Process emails to extract tasks automatically.</p>
        </div>
      ) : (
        <div className="card-list">
          {tasks.map((task) => (
            <div
              key={task.message_id}
              className="item-card"
              onClick={() => navigate(`/email/${task.message_id}`)}
            >
              <div className="item-header">
                <span className="item-title">
                  {priorityIcon(task.priority)} {task.title || task.subject}
                </span>
                <div className="btn-group">
                  <span className={`badge badge-${task.priority}`}>{task.priority}</span>
                  <span className={`badge badge-${task.status}`}>{task.status}</span>
                </div>
              </div>

              {task.action && (
                <div className="item-description">📌 {task.action}</div>
              )}

              <div className="item-meta">
                {task.category && (
                  <span className="badge badge-category">{task.category}</span>
                )}
                {task.deadline && (
                  <span style={{ fontSize: '0.78rem', color: 'var(--accent-orange)' }}>
                    ⏰ {task.deadline}
                  </span>
                )}
                {task.sender && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    From: {task.sender.length > 40 ? task.sender.substring(0, 40) + '...' : task.sender}
                  </span>
                )}
                {task.reply_required && (
                  <span className="badge badge-draft">reply needed</span>
                )}
                {task.event_required && (
                  <span className="badge badge-category">📅 event</span>
                )}
              </div>

              {task.status === 'pending' && (
                <div style={{ marginTop: '12px' }}>
                  <button
                    className="btn btn-success btn-sm"
                    onClick={(e) => handleComplete(task.message_id, e)}
                  >
                    ✓ Complete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  );
}
