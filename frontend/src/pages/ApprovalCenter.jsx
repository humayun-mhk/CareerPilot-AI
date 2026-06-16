import { useEffect, useState } from 'react';
import {
  approveApprovalItem,
  getApprovalHistory,
  getPendingApprovals,
  regenerateApprovalItem,
  rejectApprovalItem
} from '../api/client.js';

export default function ApprovalCenter() {
  const [pending, setPending] = useState([]);
  const [history, setHistory] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [notes, setNotes] = useState({});
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function load() {
    try {
      const [pendingItems, historyItems] = await Promise.all([getPendingApprovals(1), getApprovalHistory(1)]);
      setPending(pendingItems);
      setHistory(historyItems);
      setDrafts(Object.fromEntries(pendingItems.map((item) => [item.id, item.edited_content || item.original_content])));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load approval items.');
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function runAction(action, approvalId) {
    setMessage('');
    const payload = {
      approval_id: approvalId,
      edited_content: drafts[approvalId] || '',
      reviewer_notes: notes[approvalId] || ''
    };
    if (action === 'approve') await approveApprovalItem(payload);
    if (action === 'reject') await rejectApprovalItem(payload);
    if (action === 'regenerate') await regenerateApprovalItem(payload);
    setMessage(`Approval ${action} saved.`);
    await load();
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>Human Approval Center</h1>
        <p>Approve, edit, reject, or request regeneration before final resume export and application saving.</p>
      </div>
      {error && <div className="panel error">{error}</div>}
      {message && <div className="panel success">{message}</div>}

      <section className="panel">
        <h2>Pending Approvals</h2>
        {pending.length === 0 ? <p>No pending approvals.</p> : pending.map((item) => (
          <article className="approvalItem" key={item.id}>
            <div className="rowBetween">
              <h3>{item.content_type}</h3>
              <span className="badge">{item.approval_status}</span>
            </div>
            <label>
              Editable content
              <textarea
                rows="8"
                value={drafts[item.id] || ''}
                onChange={(event) => setDrafts({ ...drafts, [item.id]: event.target.value })}
              />
            </label>
            <label>
              Reviewer notes
              <input value={notes[item.id] || ''} onChange={(event) => setNotes({ ...notes, [item.id]: event.target.value })} />
            </label>
            <div className="actionRow">
              <button onClick={() => runAction('approve', item.id)}>Approve / Save Edit</button>
              <button className="secondary" onClick={() => runAction('reject', item.id)}>Reject</button>
              <button className="secondary" onClick={() => runAction('regenerate', item.id)}>Regenerate</button>
            </div>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>Approval History</h2>
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Status</th>
              <th>Updated</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item) => (
              <tr key={item.id}>
                <td>{item.content_type}</td>
                <td><span className="badge">{item.approval_status}</span></td>
                <td>{item.updated_at}</td>
                <td>{item.reviewer_notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
