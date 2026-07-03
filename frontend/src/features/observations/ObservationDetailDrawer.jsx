import { Box, Button, Chip, Divider, Drawer, Stack, Typography } from '@mui/material';
import SeverityChip from '../../components/SeverityChip';
import SourceToolChip from '../../components/SourceToolChip';
import StatusChip from '../../components/StatusChip';
import { formatDateTime } from '../../utils/formatters';
import { canWriteTechnicalRecords } from '../../utils/roleNavigation';

function Field({ label, value }) {
  return <Box><Typography variant="caption" color="text.secondary">{label}</Typography><Typography variant="body2">{value || 'Not recorded'}</Typography></Box>;
}

export default function ObservationDetailDrawer({ open, observation, role, onClose, onTriage, onPromote }) {
  const canWrite = canWriteTechnicalRecords(role);
  return (
    <Drawer anchor="right" open={open} onClose={onClose} PaperProps={{ sx: { width: { xs: '100%', sm: 520 } } }}>
      {!observation ? null : (
        <Box sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Box><Typography variant="h6">{observation.title}</Typography><StatusChip value={observation.triage_status} /></Box>
            <Divider />
            <Stack direction="row" spacing={1} flexWrap="wrap"><SourceToolChip value={observation.source_tool} /><SeverityChip value={observation.raw_severity} />{observation.confidence ? <Chip size="small" label={`${observation.confidence} confidence`} variant="outlined" /> : null}</Stack>
            <Field label="Asset/location" value={observation.raw_location || observation.url || (observation.asset ? `Asset #${observation.asset}` : '')} />
            <Field label="Evidence summary" value={observation.evidence_summary} />
            <Field label="Suggested remediation" value={observation.suggested_remediation} />
            <Field label="CVE IDs" value={(observation.cve_ids || []).join(', ')} />
            <Field label="CWE IDs" value={(observation.cwe_ids || []).join(', ')} />
            <Field label="Triage note" value={observation.triage_note} />
            <Field label="Observed" value={`${formatDateTime(observation.first_seen_at)} - ${formatDateTime(observation.last_seen_at)}`} />
            {canWrite ? <><Divider /><Stack direction="row" spacing={1} justifyContent="flex-end"><Button variant="outlined" onClick={onTriage} disabled={observation.triage_status === 'PROMOTED'}>Triage</Button><Button variant="contained" onClick={onPromote} disabled={observation.triage_status !== 'CONFIRMED'}>Promote</Button></Stack></> : null}
          </Stack>
        </Box>
      )}
    </Drawer>
  );
}
