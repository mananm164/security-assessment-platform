import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material';
import { useEffect, useState } from 'react';

export default function FindingUpdateDialog({ open, finding, loading, submitError = '', onClose, onSubmit }) {
  const [form, setForm] = useState({ status: 'OPEN', remediation_owner: '', due_date: '', business_impact: '', remediation: '', validation_evidence: '', risk_acceptance_reason: '', risk_review_due_date: '' });
  const [error, setError] = useState('');
  useEffect(() => {
    if (finding) {
      setForm({
        status: finding.status || 'OPEN',
        remediation_owner: finding.remediation_owner || '',
        due_date: finding.due_date || '',
        business_impact: finding.business_impact || '',
        remediation: finding.remediation || '',
        validation_evidence: finding.validation_evidence || '',
        risk_acceptance_reason: finding.risk_acceptance_reason || '',
        risk_review_due_date: finding.risk_review_due_date || '',
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
    if (form.status === 'ACCEPTED_RISK' && (!form.risk_acceptance_reason.trim() || !form.risk_review_due_date)) {
      setError('Accepted risk requires a reason and review due date.');
      return;
    }
    setError('');
    onSubmit({ ...form, due_date: form.due_date || null, risk_review_due_date: form.risk_review_due_date || null });
  }
  const showAcceptedRisk = form.status === 'ACCEPTED_RISK' || finding?.status === 'ACCEPTED_RISK';
  return <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth><DialogTitle>Remediation & lifecycle</DialogTitle><DialogContent><Stack spacing={2} sx={{ pt: 1 }}>{error ? <Alert severity="error">{error}</Alert> : null}{submitError ? <Alert severity="error">{submitError}</Alert> : null}<FormControl fullWidth><InputLabel id="finding-status-label">Status</InputLabel><Select labelId="finding-status-label" label="Status" value={form.status} onChange={(event) => update('status', event.target.value)}><MenuItem value="OPEN">Open</MenuItem><MenuItem value="IN_PROGRESS">In progress</MenuItem><MenuItem value="MITIGATED">Mitigated</MenuItem><MenuItem value="VALIDATION_PENDING">Validation pending</MenuItem><MenuItem value="CLOSED">Closed</MenuItem><MenuItem value="ACCEPTED_RISK">Accepted risk</MenuItem></Select></FormControl><TextField label="Remediation owner" value={form.remediation_owner} onChange={(event) => update('remediation_owner', event.target.value)} /><TextField label="Due date" type="date" value={form.due_date} onChange={(event) => update('due_date', event.target.value)} InputLabelProps={{ shrink: true }} /><TextField label="Business impact" value={form.business_impact} onChange={(event) => update('business_impact', event.target.value)} multiline minRows={3} /><TextField label="Remediation plan" value={form.remediation} onChange={(event) => update('remediation', event.target.value)} multiline minRows={3} /><TextField label="Validation evidence" value={form.validation_evidence} onChange={(event) => update('validation_evidence', event.target.value)} multiline minRows={3} helperText={form.status === 'CLOSED' ? 'Required before closing.' : 'Add concise validation evidence when available.'} />{showAcceptedRisk ? <><TextField label="Accepted-risk reason" value={form.risk_acceptance_reason} onChange={(event) => update('risk_acceptance_reason', event.target.value)} multiline minRows={3} /><TextField label="Risk review due date" type="date" value={form.risk_review_due_date} onChange={(event) => update('risk_review_due_date', event.target.value)} InputLabelProps={{ shrink: true }} /></> : null}</Stack></DialogContent><DialogActions><Button onClick={onClose} disabled={loading}>Cancel</Button><Button variant="contained" onClick={submit} disabled={loading}>Save</Button></DialogActions></Dialog>;
}
