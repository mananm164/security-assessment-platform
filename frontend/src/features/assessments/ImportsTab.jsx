import { Alert, Button, Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useEffect, useState } from 'react';
import { listImports } from '../../api/imports';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import SourceToolChip from '../../components/SourceToolChip';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDateTime } from '../../utils/formatters';

export default function ImportsTab({ assessmentId, onOpenObservations }) {
  const [state, setState] = useState({ loading: true, error: '', imports: [] });
  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try { const page = await listImports(); setState({ loading: false, error: '', imports: page.items.filter((item) => String(item.assessment) === String(assessmentId)) }); }
    catch (error) { setState({ loading: false, error: apiErrorMessage(error, 'Unable to load imports.'), imports: [] }); }
  }
  useEffect(() => { load(); }, [assessmentId]);
  if (state.loading) return <LoadingState label="Loading imports" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  return <><Alert severity="info" sx={{ mb: 2 }}>Report ingestion is currently performed through the controlled import command.</Alert>{!state.imports.length ? <EmptyState title="No imports recorded" message="Run the authorised import command to add scanner observations." /> : <Card><CardContent sx={{ p: 0 }}><Table><TableHead><TableRow><TableCell>Imported at</TableCell><TableCell>Tool</TableCell><TableCell>Filename</TableCell><TableCell>Status</TableCell><TableCell>Created</TableCell><TableCell>Re-observed</TableCell><TableCell align="right">Open observations</TableCell></TableRow></TableHead><TableBody>{state.imports.map((item) => <TableRow key={item.id}><TableCell>{formatDateTime(item.created_at)}</TableCell><TableCell><SourceToolChip value={item.source_tool} /></TableCell><TableCell>{item.source_filename}</TableCell><TableCell><StatusChip value={item.status} /></TableCell><TableCell>{item.observations_created}</TableCell><TableCell>{item.observations_updated}</TableCell><TableCell align="right"><Button size="small" onClick={onOpenObservations}>Open</Button></TableCell></TableRow>)}</TableBody></Table></CardContent></Card>}</>;
}
