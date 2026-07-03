import { Alert, Button, Card, CardContent, Divider, Grid, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { listAuditLogs } from '../../api/audit';
import { getFinding, updateFinding } from '../../api/findings';
import { useAuth } from '../../auth/AuthContext';
import AppPageHeader from '../../components/AppPageHeader';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import SeverityChip from '../../components/SeverityChip';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDate, formatDateTime } from '../../utils/formatters';
import { canWriteTechnicalRecords } from '../../utils/roleNavigation';
import AuditTimeline from './AuditTimeline';
import FindingUpdateDialog from './FindingUpdateDialog';

function Section({ title, children }) { return <Card><CardContent><Typography variant="h6">{title}</Typography><Divider sx={{ my: 1.5 }} />{children}</CardContent></Card>; }

export default function FindingDetail() {
  const { findingId } = useParams();
  const { user } = useAuth();
  const [state, setState] = useState({ loading: true, error: '', finding: null, auditLogs: [] });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const canEdit = canWriteTechnicalRecords(user?.role);

  const load = useCallback(async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try {
      const finding = await getFinding(findingId);
      const auditPage = await listAuditLogs({ entity_type: 'Finding', entity_id: findingId });
      setState({ loading: false, error: '', finding, auditLogs: auditPage.items });
    } catch (error) {
      setState({ loading: false, error: apiErrorMessage(error, 'Unable to load finding.'), finding: null, auditLogs: [] });
    }
  }, [findingId]);

  async function submitUpdate(payload) {
    setSaving(true);
    setNotice('');
    try {
      const finding = await updateFinding(findingId, payload);
      const auditPage = await listAuditLogs({ entity_type: 'Finding', entity_id: findingId });
      setState({ loading: false, error: '', finding, auditLogs: auditPage.items });
      setDialogOpen(false);
      setNotice('Finding updated.');
    } catch (error) {
      setNotice(apiErrorMessage(error, 'Unable to update finding.'));
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => { load(); }, [load]);
  if (state.loading) return <LoadingState label="Loading finding" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  const { finding, auditLogs } = state;
  return <><AppPageHeader title={finding.title} description="Finding detail for remediation tracking and audit history." action={<Stack direction="row" spacing={1}>{canEdit ? <Button variant="contained" onClick={() => setDialogOpen(true)}>Update finding</Button> : null}<Button component={RouterLink} to={`/assessments/${finding.assessment}?tab=findings`} variant="outlined">Back to assessment</Button></Stack>} />{notice ? <Alert severity={notice.includes('Unable') ? 'error' : 'success'} sx={{ mb: 2 }} aria-live="polite">{notice}</Alert> : null}<Stack spacing={2}><Card><CardContent><Grid container spacing={2}><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">CVSS</Typography><Typography variant="h5">{finding.cvss_score}</Typography></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Severity</Typography><br /><SeverityChip value={finding.severity} /></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Status</Typography><br /><StatusChip value={finding.status} /></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Due date</Typography><Typography>{formatDate(finding.due_date)}</Typography></Grid></Grid></CardContent></Card><Section title="Description"><Typography>{finding.description || 'No description recorded.'}</Typography></Section><Section title="Business impact"><Typography>{finding.business_impact || 'No business impact recorded.'}</Typography></Section><Section title="Remediation"><Typography>{finding.remediation || 'No remediation recorded.'}</Typography></Section><Section title="Ownership"><Typography color="text.secondary">Owner: {finding.remediation_owner || 'Not assigned'}</Typography><Typography color="text.secondary">Affected asset: {finding.affected_asset ? `Asset #${finding.affected_asset}` : 'Unmapped'}</Typography><Typography color="text.secondary">Created: {formatDateTime(finding.created_at)}</Typography></Section><AuditTimeline logs={auditLogs} /></Stack><FindingUpdateDialog open={dialogOpen} finding={finding} loading={saving} onClose={() => setDialogOpen(false)} onSubmit={submitUpdate} /></>;
}
