import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material';
import { useState } from 'react';

export default function ObservationTriageDialog({ open, observation, observations = [], onClose, onSubmit, loading }) {
  const [triageStatus, setTriageStatus] = useState('CONFIRMED');
  const [triageNote, setTriageNote] = useState('');
  const [duplicateOfId, setDuplicateOfId] = useState('');
  const [error, setError] = useState('');

  function handleSubmit() {
    setError('');
    if (triageStatus === 'FALSE_POSITIVE' && !triageNote.trim()) { setError('False positive triage requires a note.'); return; }
    if (triageStatus === 'DUPLICATE') {
      if (!duplicateOfId) { setError('Duplicate triage requires another observation.'); return; }
      if (String(duplicateOfId) === String(observation.id)) { setError('An observation cannot duplicate itself.'); return; }
    }
    onSubmit({ triage_status: triageStatus, triage_note: triageNote, duplicate_of_id: duplicateOfId || null });
  }

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Review observation</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {observation?.triage_status === 'PROMOTED' ? <Alert severity="info">Promoted observations cannot be triaged again.</Alert> : null}
          {error ? <Alert severity="error" aria-live="polite">{error}</Alert> : null}
          <FormControl fullWidth>
            <InputLabel id="triage-action-label">Triage action</InputLabel>
            <Select labelId="triage-action-label" label="Triage action" value={triageStatus} onChange={(event) => setTriageStatus(event.target.value)} disabled={observation?.triage_status === 'PROMOTED'}>
              <MenuItem value="CONFIRMED">Confirm observation</MenuItem>
              <MenuItem value="FALSE_POSITIVE">Mark false positive</MenuItem>
              <MenuItem value="DUPLICATE">Mark duplicate</MenuItem>
            </Select>
          </FormControl>
          {triageStatus === 'DUPLICATE' ? (
            <FormControl fullWidth>
              <InputLabel id="duplicate-target-label">Duplicate of</InputLabel>
              <Select labelId="duplicate-target-label" label="Duplicate of" value={duplicateOfId} onChange={(event) => setDuplicateOfId(event.target.value)}>
                {observations.filter((item) => String(item.id) !== String(observation?.id)).map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </Select>
            </FormControl>
          ) : null}
          <TextField label="Triage note" value={triageNote} onChange={(event) => setTriageNote(event.target.value)} multiline minRows={3} helperText="Required for false positives and recommended for all triage decisions." />
        </Stack>
      </DialogContent>
      <DialogActions><Button onClick={onClose} disabled={loading}>Cancel</Button><Button variant="contained" onClick={handleSubmit} disabled={loading || observation?.triage_status === 'PROMOTED'}>Submit</Button></DialogActions>
    </Dialog>
  );
}
