import { Button, Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { listFindings } from '../../api/findings';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import SeverityChip from '../../components/SeverityChip';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDate } from '../../utils/formatters';

export default function FindingsTab({ assessmentId }) {
  const [state, setState] = useState({ loading: true, error: '', findings: [] });
  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try { const page = await listFindings({ assessment: assessmentId }); setState({ loading: false, error: '', findings: page.items }); }
    catch (error) { setState({ loading: false, error: apiErrorMessage(error, 'Unable to load findings.'), findings: [] }); }
  }
  useEffect(() => { load(); }, [assessmentId]);
  if (state.loading) return <LoadingState label="Loading findings" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  if (!state.findings.length) return <EmptyState title="No findings yet" message="Confirmed observations can be promoted to managed findings." />;
  return <Card><CardContent sx={{ p: 0 }}><Table><TableHead><TableRow><TableCell>Title</TableCell><TableCell>Asset</TableCell><TableCell>CVSS</TableCell><TableCell>Severity</TableCell><TableCell>Status</TableCell><TableCell>Owner</TableCell><TableCell>Due date</TableCell><TableCell align="right">Open</TableCell></TableRow></TableHead><TableBody>{state.findings.map((finding) => <TableRow key={finding.id}><TableCell>{finding.title}</TableCell><TableCell>{finding.affected_asset ? `Asset #${finding.affected_asset}` : 'Unmapped'}</TableCell><TableCell>{finding.cvss_score}</TableCell><TableCell><SeverityChip value={finding.severity} /></TableCell><TableCell><StatusChip value={finding.status} /></TableCell><TableCell>{finding.remediation_owner || 'Not assigned'}</TableCell><TableCell>{formatDate(finding.due_date)}</TableCell><TableCell align="right"><Button component={RouterLink} to={`/findings/${finding.id}`} size="small">Open</Button></TableCell></TableRow>)}</TableBody></Table></CardContent></Card>;
}
