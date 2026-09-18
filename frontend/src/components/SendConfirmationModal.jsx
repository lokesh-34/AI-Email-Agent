export default function SendConfirmationModal({ draft, onConfirm, onCancel, sending }) {
  if (!draft) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>📧 Confirm Send Email</h3>

        <div className="modal-field">
          <label>To</label>
          <p>{draft.recipient}</p>
        </div>

        <div className="modal-field">
          <label>Subject</label>
          <p>{draft.subject}</p>
        </div>

        <div className="modal-field">
          <label>Message</label>
          <div className="body-preview">{draft.body}</div>
        </div>

        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onCancel} disabled={sending}>
            Cancel
          </button>
          <button className="btn btn-success" onClick={onConfirm} disabled={sending}>
            {sending ? '⏳ Sending...' : '✈️ Send Email'}
          </button>
        </div>
      </div>
    </div>
  );
}
