import { Card, CardContent, Grid, LinearProgress, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { getDashboardSummary } from '../api/dashboard';
import AppPageHeader from '../components/AppPageHeader';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import LoadingState from '../components/LoadingState';
import SeverityChip from '../components/SeverityChip';
import SourceToolChip from '../components/SourceToolChip';
import StatusChip from '../components/StatusChip';
import { apiErrorMessage } from '../utils/apiError';
import { formatDate, formatDateTime, titleCase } from '../utils/formatters';

function MetricCard({ label, value }) {
  return <Card><CardContent><Typography color="text.secondary" variant="body2">{label}</Typography><Typography variant="h4" sx={{ mt: 1 }}>{value}</Typography></CardContent></Card>;
}

function DistributionRows({ rows, kind }) {
  if (!rows?.length) return <EmptyState title="No data" message="Findings will appear here once created." />;
  const max = Math.max(...rows.map((row) => row.count || row.finding_count || 0), 1);
  return <Table size="small"><TableBody>{rows.map((row) => { const label = row.severity || row.status || row.source_tool; const count = row.count ?? row.finding_count; return <TableRow key={label}><TableCell>{kind === 'severity' ? <SeverityChip value={label} /> : kind === 'source' ? <SourceToolChip value={label} /> : <StatusChip value={label} />}</TableCell><TableCell sx={{ width: '50%' }}><LinearProgress variant="determinate" value={(count / max) * 100} /></TableCell><TableCell align="right">{count}</TableCell></TableRow>; })}</TableBody></Table>;
}

function TopPriorityTable({ rows }) {
  if (!rows?.length) return <EmptyState title="No priority data" message="Refresh CVE intelligence to compute finding priority." />;
  return <Table size="small"><TableHead><TableRow><TableCell>Finding</TableCell><TableCell>Severity</TableCell><TableCell>Priority</TableCell><TableCell>Status</TableCell><TableCell>Due</TableCell></TableRow></TableHead><TableBody>{rows.map((row) => <TableRow key={row.id} hover component={RouterLink} to={`/findings/${row.id}`} sx={{ textDecoration: 'none' }}><TableCell>{row.title}</TableCell><TableCell><SeverityChip value={row.severity} /></TableCell><TableCell>{row.priority_label ? `${titleCase(row.priority_label)} ${row.priority_score ?? ''}` : 'Not computed'}</TableCell><TableCell><StatusChip value={row.status} /></TableCell><TableCell>{formatDate(row.due_date)}</TableCell></TableRow>)}</TableBody></Table>;
}

function ActivityList({ rows }) {
  if (!rows?.length) return null;
  return <Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Recent activity</Typography><Table size="small"><TableBody>{rows.map((row) => <TableRow key={row.id}><TableCell>{row.summary}</TableCell><TableCell>{titleCase(row.action)}</TableCell><TableCell>{row.actor?.email || 'System'}</TableCell><TableCell>{formatDateTime(row.created_at)}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card>;
}

export default function DashboardPage() {
  const [state, setState] = useState({ loading: true, error: '', data: null });
  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try { const data = await getDashboardSummary(); setState({ loading: false, error: '', data }); }
    catch (error) { setState({ loading: false, error: apiErrorMessage(error, 'Unable to load dashboard.'), data: null }); }
  }
  useEffect(() => { load(); }, []);
  if (state.loading) return <LoadingState label="Loading dashboard" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  const data = state.data;
  const metrics = data.metrics || {};
  const showImports = Object.prototype.hasOwnProperty.call(metrics, 'recent_imports');
  return <><AppPageHeader title="Risk Dashboard" description="Current risk posture for the Clients you are authorised to access" /><Grid container spacing={2} sx={{ mb: 2 }}><Grid item xs={12} sm={showImports ? 3 : 4}><MetricCard label="Open findings" value={metrics.open_findings ?? data.open_findings ?? 0} /></Grid><Grid item xs={12} sm={showImports ? 3 : 4}><MetricCard label="Critical / High" value={metrics.critical_high_findings ?? data.critical_high_findings ?? 0} /></Grid><Grid item xs={12} sm={showImports ? 3 : 4}><MetricCard label="Overdue" value={metrics.overdue_remediations ?? data.overdue_remediation ?? 0} /></Grid>{showImports ? <Grid item xs={12} sm={3}><MetricCard label="Recent imports" value={metrics.recent_imports} /></Grid> : null}</Grid><Grid container spacing={2}><Grid item xs={12} md={6}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Findings by severity</Typography><DistributionRows rows={data.severity_distribution} kind="severity" /></CardContent></Card></Grid><Grid item xs={12} md={6}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Findings by remediation status</Typography><DistributionRows rows={data.status_distribution} kind="status" /></CardContent></Card></Grid><Grid item xs={12} md={5}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Findings by scanner source</Typography><DistributionRows rows={data.source_distribution} kind="source" /></CardContent></Card></Grid><Grid item xs={12} md={7}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Top priority findings</Typography><TopPriorityTable rows={data.top_priority_findings} /></CardContent></Card></Grid>{data.recent_imports?.length ? <Grid item xs={12}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Recent imports</Typography><Table size="small"><TableHead><TableRow><TableCell>Imported at</TableCell><TableCell>Tool</TableCell><TableCell>Filename</TableCell><TableCell>Status</TableCell><TableCell>Created</TableCell><TableCell>Re-observed</TableCell></TableRow></TableHead><TableBody>{data.recent_imports.map((item) => <TableRow key={item.id}><TableCell>{formatDateTime(item.created_at)}</TableCell><TableCell><SourceToolChip value={item.source_tool} /></TableCell><TableCell>{item.source_filename}</TableCell><TableCell><StatusChip value={item.status} /></TableCell><TableCell>{item.observations_created}</TableCell><TableCell>{item.observations_updated}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card></Grid> : null}{data.recent_activity?.length ? <Grid item xs={12}><ActivityList rows={data.recent_activity} /></Grid> : null}</Grid></>;
}
