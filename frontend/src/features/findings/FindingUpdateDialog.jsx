import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material';
import { useEffect, useState } from 'react';

export default function FindingUpdateDialog({ open, finding, loading, onClose, onSubmit }) {
  const [form, setForm] = useState({ status: 'OPEN', remediation_owner: '', due_date: '', business_impact: '', remediation: '' });
  const [error, setError] = useState('');
  useEffect(() => {
    if (finding) {
      setForm({
        status: finding.status || 'OPEN',
        remediation_owner: finding.remediation_owner || '',
        due_date: finding.due_date || '',
        business_impact: finding.business_impact || '',
        remediation: finding.remediation || '',
      });
      setError('');
    }
  }, [finding, open]);
  function update(field, value) { setForm((current) => ({ ...current, [field]: value })); }
  function submit() {
    if (!form.business_impact.trim() || !form.remediation.trim()) {
      setError('Business impact and remediation notes are required.');
      return;
    }
    onSubmit({ ...form, due_date: form.due_date || null });
  }
  return <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth><DialogTitle>Update finding</DialogTitle><DialogContent><Stack spacing={2} sx={{ pt: 1 }}>{error ? <Alert severity="error">{error}</Alert> : null}<FormControl fullWidth><InputLabel id="finding-status-label">Status</InputLabel><Select labelId="finding-status-label" label="Status" value={form.status} onChange={(event) => update('status', event.target.value)}><MenuItem value="OPEN">Open</MenuItem><MenuItem value="IN_PROGRESS">In progress</MenuItem><MenuItem value="ACCEPTED_RISK">Accepted risk</MenuItem><MenuItem value="MITIGATED">Mitigated</MenuItem><MenuItem value="CLOSED">Closed</MenuItem></Select></FormControl><TextField label="Remediation owner" value={form.remediation_owner} onChange={(event) => update('remediation_owner', event.target.value)} /><TextField label="Due date" type="date" value={form.due_date} onChange={(event) => update('due_date', event.target.value)} InputLabelProps={{ shrink: true }} /><TextField label="Business impact" value={form.business_impact} onChange={(event) => update('business_impact', event.target.value)} multiline minRows={3} /><TextField label="Remediation notes" value={form.remediation} onChange={(event) => update('remediation', event.target.value)} multiline minRows={3} /></Stack></DialogContent><DialogActions><Button onClick={onClose} disabled={loading}>Cancel</Button><Button variant="contained" onClick={submit} disabled={loading}>Save</Button></DialogActions></Dialog>;
}
