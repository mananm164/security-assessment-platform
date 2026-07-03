import { Card, CardContent, Divider, Stack, Typography } from '@mui/material';
import { formatDateTime, titleCase } from '../../utils/formatters';

export default function AuditTimeline({ logs = [] }) {
  return <Card><CardContent><Typography variant="h6">Audit timeline</Typography><Divider sx={{ my: 1.5 }} />{logs.length ? <Stack spacing={1.5}>{logs.map((log) => <Stack key={log.id} spacing={0.25}><Typography variant="body2">{log.summary}</Typography><Typography variant="caption" color="text.secondary">{formatDateTime(log.created_at)} · {titleCase(log.action)} · {log.actor || 'System'}</Typography></Stack>)}</Stack> : <Typography color="text.secondary">No audit events recorded for this finding yet.</Typography>}</CardContent></Card>;
}
