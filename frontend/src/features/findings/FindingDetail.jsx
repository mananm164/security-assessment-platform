import { Button, Card, CardContent, Divider, Grid, Stack, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getFinding } from '../../api/findings';
import AppPageHeader from '../../components/AppPageHeader';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import SeverityChip from '../../components/SeverityChip';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDate, formatDateTime } from '../../utils/formatters';

function Section({ title, children }) { return <Card><CardContent><Typography variant="h6">{title}</Typography><Divider sx={{ my: 1.5 }} />{children}</CardContent></Card>; }

export default function FindingDetail() {
  const { findingId } = useParams();
  const [state, setState] = useState({ loading: true, error: '', finding: null });
  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try { const finding = await getFinding(findingId); setState({ loading: false, error: '', finding }); }
    catch (error) { setState({ loading: false, error: apiErrorMessage(error, 'Unable to load finding.'), finding: null }); }
  }
  useEffect(() => { load(); }, [findingId]);
  if (state.loading) return <LoadingState label="Loading finding" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  const { finding } = state;
  return <><AppPageHeader title={finding.title} description="Read-only finding detail for remediation tracking." action={<Button component={RouterLink} to={`/assessments/${finding.assessment}?tab=findings`} variant="outlined">Back to assessment</Button>} /><Stack spacing={2}><Card><CardContent><Grid container spacing={2}><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">CVSS</Typography><Typography variant="h5">{finding.cvss_score}</Typography></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Severity</Typography><br /><SeverityChip value={finding.severity} /></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Status</Typography><br /><StatusChip value={finding.status} /></Grid><Grid item xs={12} sm={3}><Typography variant="caption" color="text.secondary">Due date</Typography><Typography>{formatDate(finding.due_date)}</Typography></Grid></Grid></CardContent></Card><Section title="Description"><Typography>{finding.description || 'No description recorded.'}</Typography></Section><Section title="Business impact"><Typography>{finding.business_impact || 'No business impact recorded.'}</Typography></Section><Section title="Remediation"><Typography>{finding.remediation || 'No remediation recorded.'}</Typography></Section><Section title="Ownership"><Typography color="text.secondary">Owner: {finding.remediation_owner || 'Not assigned'}</Typography><Typography color="text.secondary">Affected asset: {finding.affected_asset ? `Asset #${finding.affected_asset}` : 'Unmapped'}</Typography><Typography color="text.secondary">Created: {formatDateTime(finding.created_at)}</Typography></Section></Stack></>;
}
