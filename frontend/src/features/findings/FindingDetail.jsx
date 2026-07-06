import { Alert, Button, Card, CardContent, Divider, Grid, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { generateRemediationDraft, listAIArtifacts } from '../../api/ai';
import { getFindingIntelligence, refreshFindingIntelligence } from '../../api/intelligence';
import { getFinding, listFindingAuditLogs, updateFinding } from '../../api/findings';
import { useAuth } from '../../auth/AuthContext';
import AppPageHeader from '../../components/AppPageHeader';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import SeverityChip from '../../components/SeverityChip';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDate, formatDateTime } from '../../utils/formatters';
import { canSeeRawScannerData, canWriteTechnicalRecords } from '../../utils/roleNavigation';
import AuditTimeline from './AuditTimeline';
import IntelligencePanel from './IntelligencePanel';
import FindingUpdateDialog from './FindingUpdateDialog';
import RemediationDraftPanel from './RemediationDraftPanel';

function Section({ title, children }) { return <Card><CardContent><Typography variant="h6">{title}</Typography><Divider sx={{ my: 1.5 }} />{children}</CardContent></Card>; }

export default function FindingDetail() {
  const { findingId } = useParams();
  const { user } = useAuth();
  const [state, setState] = useState({ loading: true, error: '', finding: null, auditLogs: [], intelligence: null, aiArtifacts: [] });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [dialogError, setDialogError] = useState('');
  const [intelligenceBusy, setIntelligenceBusy] = useState(false);
  const [intelligenceError, setIntelligenceError] = useState('');
  const [aiBusy, setAiBusy] = useState(false);
  const [aiError, setAiError] = useState('');
  const canEdit = canWriteTechnicalRecords(user?.role);
  const canViewActivity = canSeeRawScannerData(user?.role);

  const load = useCallback(async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try {
      const finding = await getFinding(findingId);
      const [auditPage, intelligencePayload, aiArtifacts] = await Promise.all([
        canViewActivity ? listFindingAuditLogs(findingId) : Promise.resolve({ items: [] }),
        getFindingIntelligence(findingId),
        listAIArtifacts(findingId),
      ]);
      setState({ loading: false, error: '', finding: intelligencePayload.finding || finding, auditLogs: auditPage.items, intelligence: intelligencePayload.intelligence, aiArtifacts });
    } catch (error) {
      setState({ loading: false, error: apiErrorMessage(error, 'Unable to load finding.'), finding: null, auditLogs: [], intelligence: null, aiArtifacts: [] });
    }
  }, [findingId, canViewActivity]);

  async function submitUpdate(payload) {
    setSaving(true);
    setNotice('');
    setDialogError('');
    try {
      const finding = await updateFinding(findingId, payload);
      const auditPage = canViewActivity ? await listFindingAuditLogs(findingId) : { items: [] };
      setState((current) => ({ ...current, loading: false, error: '', finding, auditLogs: auditPage.items }));
      setDialogOpen(false);
      setNotice('Finding updated.');
    } catch (error) {
      setDialogError(apiErrorMessage(error, 'Unable to update finding.'));
      setNotice('Unable to update finding.');
    } finally {
      setSaving(false);
    }
  }



  async function refreshIntelligence() {
    setIntelligenceBusy(true);
    setIntelligenceError('');
    try {
      const payload = await refreshFindingIntelligence(findingId);
      const auditPage = canViewActivity ? await listFindingAuditLogs(findingId) : { items: [] };
      setState((current) => ({ ...current, finding: payload.finding, intelligence: payload.intelligence, auditLogs: auditPage.items }));
      setNotice(payload.used_cache ? 'Using cached intelligence.' : 'Intelligence refreshed.');
    } catch (error) {
      setIntelligenceError(apiErrorMessage(error, 'Unable to refresh intelligence.'));
    } finally {
      setIntelligenceBusy(false);
    }
  }

  async function generateDraft() {
    setAiBusy(true);
    setAiError('');
    try {
      const artifact = await generateRemediationDraft(findingId);
      const auditPage = canViewActivity ? await listFindingAuditLogs(findingId) : { items: [] };
      setState((current) => ({ ...current, aiArtifacts: [artifact, ...current.aiArtifacts.filter((item) => item.id !== artifact.id)], auditLogs: auditPage.items }));
      setNotice('Remediation draft generated.');
    } catch (error) {
      setAiError(apiErrorMessage(error, 'Unable to generate remediation draft.'));
    } finally {
      setAiBusy(false);
    }
  }

  useEffect(() => { load(); }, [load]);
  if (state.loading) return <LoadingState label="Loading finding" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  const { finding, auditLogs, intelligence, aiArtifacts } = state;
  return <><AppPageHeader title={finding.title} description="Finding detail for remediation tracking and audit history." action={<Stack direction="row" spacing={1}>{canEdit ? <Button variant="contained" onClick={() => setDialogOpen(true)}>Update finding</Button> : null}<Button component={RouterLink} to={`/assessments/${finding.assessment}?tab=findings`} variant="outlined">Back to assessment</Button></Stack>} />{notice ? <Alert severity={notice.includes('Unable') ? 'error' : 'success'} sx={{ mb: 2 }} aria-live="polite">{notice}</Alert> : null}<Stack spacing={2}><IntelligencePanel finding={finding} intelligence={intelligence} loading={intelligenceBusy} error={intelligenceError} canEdit={canEdit} onRefresh={refreshIntelligence} /><RemediationDraftPanel artifacts={aiArtifacts} loading={aiBusy} error={aiError} canEdit={canEdit} onGenerate={generateDraft} /><Card><CardContent><Grid container spacing={2}><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">CVSS</Typography><Typography variant="h5">{finding.cvss_score}</Typography></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Severity</Typography><br /><SeverityChip value={finding.severity} /></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Status</Typography><br /><StatusChip value={finding.status} /></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Due date</Typography><Typography>{formatDate(finding.due_date)}</Typography></Grid></Grid></CardContent></Card><Section title="Description"><Typography>{finding.description || 'No description recorded.'}</Typography></Section><Section title="Business impact"><Typography>{finding.business_impact || 'No business impact recorded.'}</Typography></Section><Section title="Remediation & lifecycle"><Stack spacing={1}><Typography>{finding.remediation || 'No remediation recorded.'}</Typography><Typography color="text.secondary">Owner: {finding.remediation_owner || 'Not assigned'}</Typography><Typography color="text.secondary">Due date: {formatDate(finding.due_date)}</Typography><Typography color="text.secondary">Validation evidence: {finding.validation_evidence || 'Not recorded'}</Typography>{finding.status === 'ACCEPTED_RISK' ? <Typography color="text.secondary">Accepted risk review due: {formatDate(finding.risk_review_due_date)}</Typography> : null}{finding.risk_acceptance_reason ? <Typography color="text.secondary">Accepted-risk reason: {finding.risk_acceptance_reason}</Typography> : null}</Stack></Section><Section title="Ownership"><Typography color="text.secondary">Affected asset: {finding.affected_asset ? `Asset #${finding.affected_asset}` : 'Unmapped'}</Typography><Typography color="text.secondary">Created: {formatDateTime(finding.created_at)}</Typography><Typography color="text.secondary">Validated by: {finding.validated_by || 'Not validated'}</Typography><Typography color="text.secondary">Risk accepted by: {finding.risk_accepted_by || 'Not accepted'}</Typography></Section>{canViewActivity ? <AuditTimeline logs={auditLogs} /> : null}</Stack><FindingUpdateDialog open={dialogOpen} finding={finding} loading={saving} submitError={dialogError} onClose={() => setDialogOpen(false)} onSubmit={submitUpdate} /></>;
}
