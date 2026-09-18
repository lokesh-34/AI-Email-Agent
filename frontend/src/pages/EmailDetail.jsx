import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getEmail, getTask } from '../api/api';

export default function EmailDetail() {
  const { messageId } = useParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState(null);
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [messageId]);

  async function loadData() {
    setLoading(true);
    try {
      const [emailData, taskData] = await Promise.all([
        getEmail(messageId).catch(() => null),
        getTask(messageId).catch(() => null),
      ]);
      setEmail(emailData);
      setTask(taskData);
    } catch (err) {
      console.error('Failed to load email:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Loading email...
      </div>
    );
  }

  if (!email && !task) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📧</div>
        <h3>Email not found</h3>
        <p>Could not load this email.</p>
        <button className="btn btn-ghost" onClick={() => navigate(-1)}>← Go Back</button>
      </div>
    );
  }

  return (
    <div>
      <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)} style={{ marginBottom: '20px' }}>
        ← Back
      </button>

      <div className="email-detail">
        {/* Main email content */}
        <div>
          <div className="email-body-card">
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ fontSize: '1.3rem', marginBottom: '8px' }}>
                {email?.subject || task?.subject || 'No Subject'}
              </h2>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                From: {email?.sender || task?.sender}
              </div>
              {(email?.date || task?.date) && (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
                  {email?.date || task?.date}
                </div>
              )}
            </div>

            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
              <div className="email-body-text">
                {email?.body || 'Email body not available.'}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar with AI analysis */}
        <div className="email-sidebar">
          {task && (
            <>
              <div className="card">
                <h3 style={{ fontSize: '0.9rem', marginBottom: '14px' }}>🤖 AI Analysis</h3>
                <div className="info-row">
                  <span className="info-label">Category</span>
                  <span className="badge badge-category">{task.category}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Priority</span>
                  <span className={`badge badge-${task.priority}`}>{task.priority}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Status</span>
                  <span className={`badge badge-${task.status}`}>{task.status}</span>
                </div>
                {task.action && (
                  <div className="info-row">
                    <span className="info-label">Action</span>
                    <span style={{ fontSize: '0.85rem', textAlign: 'right', maxWidth: '180px' }}>{task.action}</span>
                  </div>
                )}
                {task.deadline && (
                  <div className="info-row">
                    <span className="info-label">Deadline</span>
                    <span style={{ color: 'var(--accent-orange)', fontSize: '0.85rem' }}>{task.deadline}</span>
                  </div>
                )}
              </div>

              {task.event_required && (
                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', marginBottom: '14px' }}>📅 Calendar Event</h3>
                  {task.event_title && (
                    <div className="info-row">
                      <span className="info-label">Event</span>
                      <span style={{ fontSize: '0.85rem' }}>{task.event_title}</span>
                    </div>
                  )}
                  {task.event_date && (
                    <div className="info-row">
                      <span className="info-label">Date</span>
                      <span>{task.event_date}</span>
                    </div>
                  )}
                  {task.event_start_time && (
                    <div className="info-row">
                      <span className="info-label">Time</span>
                      <span>{task.event_start_time}{task.event_end_time ? ` - ${task.event_end_time}` : ''}</span>
                    </div>
                  )}
                  {task.event_timezone && (
                    <div className="info-row">
                      <span className="info-label">Timezone</span>
                      <span>{task.event_timezone}</span>
                    </div>
                  )}
                  {task.event_location && (
                    <div className="info-row">
                      <span className="info-label">Location</span>
                      <span>{task.event_location}</span>
                    </div>
                  )}
                  {task.calendar_event_id && (
                    <div style={{ marginTop: '10px', fontSize: '0.78rem', color: 'var(--accent-green)' }}>
                      ✅ Event created in Google Calendar
                    </div>
                  )}
                </div>
              )}

              {task.reply_required && (
                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', marginBottom: '14px' }}>✉️ Reply</h3>
                  <div className="info-row">
                    <span className="info-label">Required</span>
                    <span style={{ color: 'var(--accent-warm)' }}>Yes</span>
                  </div>
                  {task.reply_type && (
                    <div className="info-row">
                      <span className="info-label">Type</span>
                      <span className="badge badge-category">{task.reply_type}</span>
                    </div>
                  )}
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ marginTop: '12px', width: '100%', justifyContent: 'center' }}
                    onClick={() => navigate('/drafts')}
                  >
                    View Draft →
                  </button>
                </div>
              )}

              {task.ai_explanation && (
                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', marginBottom: '10px' }}>💡 AI Insight</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {task.ai_explanation}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
