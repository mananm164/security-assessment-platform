import { Card, CardContent, Divider, Stack, Typography } from '@mui/material';
import { formatDateTime, titleCase } from '../../utils/formatters';

function actorLabel(actor) {
  if (!actor) return 'System';
  if (typeof actor === 'string') return actor;
  return actor.email || `User #${actor.id}`;
}

function describe(log) {
  const metadata = log.safe_metadata || log.metadata || {};
  if (log.action === 'FINDING_STATUS_CHANGED') return `Status changed: ${titleCase(metadata.old_status)} to ${titleCase(metadata.new_status)}`;
  if (log.action === 'FINDING_OWNER_CHANGED') return `Owner changed: ${metadata.old_remediation_owner || 'Unassigned'} to ${metadata.new_remediation_owner || 'Unassigned'}`;
  if (log.action === 'FINDING_DUE_DATE_CHANGED') return `Due date changed: ${metadata.old_due_date || 'Not set'} to ${metadata.new_due_date || 'Not set'}`;
  if (log.action === 'FINDING_CLOSED') return 'Finding closed with validation evidence';
  if (log.action === 'FINDING_RISK_ACCEPTED') return 'Risk accepted pending review';
  if (log.action === 'FINDING_REOPENED') return 'Finding reopened';
  if (log.action === 'AI_REMEDIATION_DRAFT_GENERATED') return 'AI remediation draft generated';
  if (log.action === 'INTELLIGENCE_REFRESHED') return 'CVE intelligence refreshed';
  return log.summary || 'Finding updated';
}

export default function AuditTimeline({ logs = [], title = 'Activity' }) {
  return <Card><CardContent><Typography variant="h6">{title}</Typography><Divider sx={{ my: 1.5 }} />{logs.length ? <Stack spacing={1.5}>{logs.map((log) => <Stack key={log.id} spacing={0.25}><Typography variant="body2">{describe(log)}</Typography><Typography variant="caption" color="text.secondary">{formatDateTime(log.created_at)} · {titleCase(log.action)} · {actorLabel(log.actor)}</Typography></Stack>)}</Stack> : <Typography color="text.secondary">No activity recorded for this finding yet.</Typography>}</CardContent></Card>;
}
