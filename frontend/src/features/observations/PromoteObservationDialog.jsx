import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField } from '@mui/material';
import { useState } from 'react';

export default function PromoteObservationDialog({ open, observation, onClose, onSubmit, loading }) {
  const [form, setForm] = useState({ title: observation?.title || '', cvss_score: '', business_impact: '', remediation_owner: '', due_date: '' });
  const [error, setError] = useState('');

  function update(field, value) { setForm((current) => ({ ...current, [field]: value })); }
  function handleSubmit() {
    setError('');
    const cvss = Number(form.cvss_score);
    if (Number.isNaN(cvss) || cvss < 0 || cvss > 10) { setError('CVSS score must be between 0.0 and 10.0.'); return; }
    if (!form.business_impact.trim() || !form.remediation_owner.trim() || !form.due_date) { setError('Business impact, remediation owner and due date are required.'); return; }
    onSubmit(form);
  }

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Promote to finding</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {observation?.triage_status !== 'CONFIRMED' ? <Alert severity="warning">Only confirmed observations can be promoted.</Alert> : null}
          {error ? <Alert severity="error" aria-live="polite">{error}</Alert> : null}
          <TextField label="Finding title" value={form.title} onChange={(event) => update('title', event.target.value)} />
          <TextField label="Consultant-reviewed CVSS score" value={form.cvss_score} onChange={(event) => update('cvss_score', event.target.value)} helperText="The backend derives final severity from this reviewed score." />
          <TextField label="Business impact" value={form.business_impact} onChange={(event) => update('business_impact', event.target.value)} multiline minRows={3} />
          <TextField label="Remediation owner" value={form.remediation_owner} onChange={(event) => update('remediation_owner', event.target.value)} />
          <TextField label="Due date" type="date" value={form.due_date} onChange={(event) => update('due_date', event.target.value)} InputLabelProps={{ shrink: true }} />
        </Stack>
      </DialogContent>
      <DialogActions><Button onClick={onClose} disabled={loading}>Cancel</Button><Button variant="contained" onClick={handleSubmit} disabled={loading || observation?.triage_status !== 'CONFIRMED'}>Promote</Button></DialogActions>
    </Dialog>
  );
}
