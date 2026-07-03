import { Card, CardContent, Grid, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { getDashboardSummary } from '../api/dashboard';
import AppPageHeader from '../components/AppPageHeader';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import LoadingState from '../components/LoadingState';
import SeverityChip from '../components/SeverityChip';
import SourceToolChip from '../components/SourceToolChip';
import StatusChip from '../components/StatusChip';
import { apiErrorMessage } from '../utils/apiError';
import { formatDateTime } from '../utils/formatters';

function MetricCard({ label, value }) {
  return <Card><CardContent><Typography color="text.secondary" variant="body2">{label}</Typography><Typography variant="h4" sx={{ mt: 1 }}>{value}</Typography></CardContent></Card>;
}

function SeverityRows({ data }) {
  const rows = Object.entries(data || {});
  if (!rows.length) return <EmptyState title="No severity data" message="Findings will appear here once created." />;
  return <Table size="small"><TableBody>{rows.map(([severity, count]) => <TableRow key={severity}><TableCell><SeverityChip value={severity} /></TableCell><TableCell align="right">{count}</TableCell></TableRow>)}</TableBody></Table>;
}

function SourceRows({ data }) {
  const rows = Object.entries(data || {});
  if (!rows.length) return <EmptyState title="No source data" message="Promoted scanner observations will populate this view." />;
  return <Table size="small"><TableBody>{rows.map(([source, count]) => <TableRow key={source}><TableCell><SourceToolChip value={source} /></TableCell><TableCell align="right">{count}</TableCell></TableRow>)}</TableBody></Table>;
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
  return <><AppPageHeader title="Dashboard" description="Operational view of visible findings, remediation urgency and recent imports." /><Grid container spacing={2} sx={{ mb: 2 }}><Grid item xs={12} sm={4}><MetricCard label="Open findings" value={data.open_findings} /></Grid><Grid item xs={12} sm={4}><MetricCard label="Critical/high findings" value={data.critical_high_findings} /></Grid><Grid item xs={12} sm={4}><MetricCard label="Overdue remediation" value={data.overdue_remediation} /></Grid></Grid><Grid container spacing={2}><Grid item xs={12} md={6}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Findings by severity</Typography><SeverityRows data={data.findings_by_severity} /></CardContent></Card></Grid><Grid item xs={12} md={6}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Findings by scanner source</Typography><SourceRows data={data.findings_by_scanner_source} /></CardContent></Card></Grid><Grid item xs={12}><Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Recent imports</Typography>{data.recent_imports?.length ? <Table size="small"><TableHead><TableRow><TableCell>Imported at</TableCell><TableCell>Tool</TableCell><TableCell>Filename</TableCell><TableCell>Status</TableCell><TableCell>Created</TableCell><TableCell>Re-observed</TableCell></TableRow></TableHead><TableBody>{data.recent_imports.map((item) => <TableRow key={item.id}><TableCell>{formatDateTime(item.created_at)}</TableCell><TableCell><SourceToolChip value={item.source_tool} /></TableCell><TableCell>{item.source_filename}</TableCell><TableCell><StatusChip value={item.status} /></TableCell><TableCell>{item.observations_created}</TableCell><TableCell>{item.observations_updated}</TableCell></TableRow>)}</TableBody></Table> : <EmptyState title="No recent imports" message="Client users may not see raw import history; consultants can import reports through the controlled command." />}</CardContent></Card></Grid></Grid></>;
}
