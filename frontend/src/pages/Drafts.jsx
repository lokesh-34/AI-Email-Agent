import { useState, useEffect } from 'react';
import { getDrafts, getDraft, updateDraft, sendDraft, rejectDraft } from '../api/api';
import SendConfirmationModal from '../components/SendConfirmationModal';
import Toast from '../components/Toast';

export default function Drafts() {
  const [drafts, setDrafts] = useState([]);
  const [filter, setFilter] = useState('draft');
  const [loading, setLoading] = useState(true);
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [showSendModal, setShowSendModal] = useState(false);
  const [sending, setSending] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadDrafts();
  }, [filter]);

  async function loadDrafts() {
    setLoading(true);
    try {
      const data = await getDrafts(filter === 'all' ? null : filter);
      setDrafts(data);
    } catch (err) {
      console.error('Failed to load drafts:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectDraft(draft) {
    try {
      const full = await getDraft(draft.draft_id);
      setSelectedDraft(full);
      setEditing(false);
    } catch (err) {
      setToast({ message: err.message, type: 'error' });
    }
  }

  function handleEdit() {
    setEditing(true);
    setEditData({
      recipient: selectedDraft.recipient || '',
      subject: selectedDraft.subject || '',
      body: selectedDraft.body || '',
    });
  }

  async function handleSaveEdit() {
    try {
      const updated = await updateDraft(selectedDraft.draft_id, editData);
      setSelectedDraft(updated);
      setEditing(false);
      setToast({ message: 'Draft updated!', type: 'success' });
      loadDrafts();
    } catch (err) {
      setToast({ message: err.message, type: 'error' });
    }
  }

  function handleReviewAndSend() {
    setShowSendModal(true);
  }

  async function handleConfirmSend() {
    setSending(true);
    try {
      const result = await sendDraft(selectedDraft.draft_id);
      setToast({ message: result.message, type: 'success' });
      setShowSendModal(false);
      setSelectedDraft(null);
      loadDrafts();
    } catch (err) {
      setToast({ message: err.message, type: 'error' });
    } finally {
      setSending(false);
    }
  }

  async function handleReject(draftId) {
    try {
      await rejectDraft(draftId);
      setToast({ message: 'Draft rejected.', type: 'info' });
      setSelectedDraft(null);
      loadDrafts();
    } catch (err) {
      setToast({ message: err.message, type: 'error' });
    }
  }

  const statusIcon = (s) => {
    const icons = { draft: '📝', approved: '✅', sent: '✈️', rejected: '❌' };
    return icons[s] || '📄';
  };

  // Detail view
  if (selectedDraft) {
    return (
      <div>
        <button className="btn btn-ghost btn-sm" onClick={() => setSelectedDraft(null)} style={{ marginBottom: '20px' }}>
          ← Back to Drafts
        </button>

        <div className="page-header">
          <h2>AI Generated Reply</h2>
          <p>Review, edit, and send this draft</p>
        </div>

        <div className="card" style={{ maxWidth: '700px' }}>
          {editing ? (
            <>
              <div className="form-group">
                <label className="form-label">To</label>
                <input
                  className="form-input"
                  value={editData.recipient}
                  onChange={(e) => setEditData({ ...editData, recipient: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Subject</label>
                <input
                  className="form-input"
                  value={editData.subject}
                  onChange={(e) => setEditData({ ...editData, subject: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Body</label>
                <textarea
                  className="form-textarea"
                  value={editData.body}
                  onChange={(e) => setEditData({ ...editData, body: e.target.value })}
                  rows={10}
                />
              </div>
              <div className="btn-group">
                <button className="btn btn-primary" onClick={handleSaveEdit}>💾 Save Changes</button>
                <button className="btn btn-ghost" onClick={() => setEditing(false)}>Cancel</button>
              </div>
            </>
          ) : (
            <>
              <div style={{ marginBottom: '16px' }}>
                <div className="form-label">To</div>
                <div style={{ fontSize: '0.95rem' }}>{selectedDraft.recipient}</div>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <div className="form-label">Subject</div>
                <div style={{ fontSize: '0.95rem' }}>{selectedDraft.subject}</div>
              </div>
              {selectedDraft.reply_type && (
                <div style={{ marginBottom: '16px' }}>
                  <div className="form-label">Reply Type</div>
                  <span className="badge badge-category">{selectedDraft.reply_type}</span>
                </div>
              )}
              <div style={{ marginBottom: '20px' }}>
                <div className="form-label">Message</div>
                <div style={{
                  background: 'var(--bg-input)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  fontSize: '0.9rem',
                  lineHeight: '1.7',
                  whiteSpace: 'pre-wrap',
                  marginTop: '6px'
                }}>
                  {selectedDraft.body}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '20px' }}>
                <span className="form-label" style={{ marginBottom: 0 }}>Status</span>
                <span className={`badge badge-${selectedDraft.status}`}>{selectedDraft.status}</span>
              </div>

              {selectedDraft.status !== 'sent' && selectedDraft.status !== 'rejected' && (
                <div className="btn-group">
                  <button className="btn btn-ghost" onClick={handleEdit}>✏️ Edit Draft</button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleReject(selectedDraft.draft_id)}>
                    ❌ Reject
                  </button>
                  <button className="btn btn-success" onClick={handleReviewAndSend}>
                    ✈️ Review & Send
                  </button>
                </div>
              )}

              {selectedDraft.status === 'sent' && (
                <div style={{
                  padding: '12px 16px',
                  background: 'var(--status-sent-bg)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--status-sent)',
                  fontSize: '0.85rem',
                  fontWeight: 600
                }}>
                  ✅ This email has been sent.
                  {selectedDraft.sent_at && ` (${selectedDraft.sent_at})`}
                </div>
              )}
            </>
          )}
        </div>

        {showSendModal && (
          <SendConfirmationModal
            draft={selectedDraft}
            onConfirm={handleConfirmSend}
            onCancel={() => setShowSendModal(false)}
            sending={sending}
          />
        )}

        {toast && (
          <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
        )}
      </div>
    );
  }

  // List view
  return (
    <div>
      <div className="page-header">
        <h2>Email Drafts</h2>
        <p>AI-generated replies awaiting your review</p>
      </div>

      <div className="filter-tabs">
        {['draft', 'approved', 'sent', 'rejected', 'all'].map((f) => (
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
          Loading drafts...
        </div>
      ) : drafts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✉️</div>
          <h3>No {filter} drafts</h3>
          <p>AI-generated reply drafts will appear here after processing emails.</p>
        </div>
      ) : (
        <div className="card-list">
          {drafts.map((draft) => (
            <div
              key={draft.draft_id}
              className="item-card"
              onClick={() => handleSelectDraft(draft)}
            >
              <div className="item-header">
                <span className="item-title">
                  {statusIcon(draft.status)} {draft.subject || 'No subject'}
                </span>
                <span className={`badge badge-${draft.status}`}>{draft.status}</span>
              </div>
              <div className="item-description">
                To: {draft.recipient}
              </div>
              <div className="item-meta">
                {draft.reply_type && (
                  <span className="badge badge-category">{draft.reply_type}</span>
                )}
                {draft.created_at && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(draft.created_at).toLocaleString()}
                  </span>
                )}
              </div>
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
