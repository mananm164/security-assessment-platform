import { Alert, Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listObservations, promoteObservation, triageObservation } from '../../api/observations';
import { useAuth } from '../../auth/AuthContext';
import DataTableToolbar from '../../components/DataTableToolbar';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import SeverityChip from '../../components/SeverityChip';
import SourceToolChip from '../../components/SourceToolChip';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDateTime } from '../../utils/formatters';
import ObservationDetailDrawer from '../observations/ObservationDetailDrawer';
import ObservationTriageDialog from '../observations/ObservationTriageDialog';
import PromoteObservationDialog from '../observations/PromoteObservationDialog';

export function ObservationsTable({ observations, onOpen }) {
  return <Card><CardContent sx={{ p: 0 }}><Table aria-label="Scanner observations table"><TableHead><TableRow><TableCell>Title</TableCell><TableCell>Tool</TableCell><TableCell>Asset/location</TableCell><TableCell>Scanner severity</TableCell><TableCell>Triage status</TableCell><TableCell>Confidence</TableCell><TableCell>Observed</TableCell></TableRow></TableHead><TableBody>{observations.map((item) => <TableRow key={item.id} hover tabIndex={0} onClick={() => onOpen(item)} sx={{ cursor: 'pointer' }}><TableCell>{item.title}</TableCell><TableCell><SourceToolChip value={item.source_tool} /></TableCell><TableCell>{item.raw_location || item.url || (item.asset ? `Asset #${item.asset}` : 'Unmapped')}</TableCell><TableCell><SeverityChip value={item.raw_severity} /></TableCell><TableCell><StatusChip value={item.triage_status} /></TableCell><TableCell>{item.confidence || 'Not recorded'}</TableCell><TableCell>{formatDateTime(item.last_seen_at)}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card>;
}

export default function ObservationsTab({ assessmentId }) {
  const [state, setState] = useState({ loading: true, error: '', observations: [] });
  const [sourceTool, setSourceTool] = useState('');
  const [triageStatus, setTriageStatus] = useState('');
  const [selected, setSelected] = useState(null);
  const [triageOpen, setTriageOpen] = useState(false);
  const [promoteOpen, setPromoteOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try { const page = await listObservations({ assessment: assessmentId, ...(sourceTool ? { source_tool: sourceTool } : {}) }); setState({ loading: false, error: '', observations: page.items }); }
    catch (error) { setState({ loading: false, error: apiErrorMessage(error, 'Unable to load observations.'), observations: [] }); }
  }
  useEffect(() => { load(); }, [assessmentId, sourceTool]);
  const filtered = useMemo(() => state.observations.filter((item) => !triageStatus || item.triage_status === triageStatus), [state.observations, triageStatus]);

  async function submitTriage(payload) {
    setSaving(true);
    try { const updated = await triageObservation(selected.id, payload); setSelected(updated); setTriageOpen(false); setNotice('Observation updated.'); await load(); }
    catch (error) { setNotice(apiErrorMessage(error, 'Unable to update observation.')); }
    finally { setSaving(false); }
  }
  async function submitPromote(payload) {
    setSaving(true);
    try { const finding = await promoteObservation(selected.id, payload); setPromoteOpen(false); setNotice('Finding created.'); navigate(`/findings/${finding.id}`); }
    catch (error) { setNotice(apiErrorMessage(error, 'Unable to promote observation.')); }
    finally { setSaving(false); }
  }

  if (state.loading) return <LoadingState label="Loading scanner observations" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  return <><DataTableToolbar sourceTool={sourceTool} triageStatus={triageStatus} onSourceToolChange={setSourceTool} onTriageStatusChange={setTriageStatus} />{notice ? <Alert severity={notice.includes('Unable') ? 'error' : 'success'} sx={{ mb: 2 }} aria-live="polite">{notice}</Alert> : null}{!filtered.length ? <EmptyState title="No scanner observations match these filters" message="Clear filters or import an authorised report through the controlled import process." /> : <ObservationsTable observations={filtered} onOpen={setSelected} />}<ObservationDetailDrawer open={Boolean(selected)} observation={selected} role={user?.role} onClose={() => setSelected(null)} onTriage={() => setTriageOpen(true)} onPromote={() => setPromoteOpen(true)} /><ObservationTriageDialog open={triageOpen} observation={selected} observations={state.observations} onClose={() => setTriageOpen(false)} onSubmit={submitTriage} loading={saving} /><PromoteObservationDialog open={promoteOpen} observation={selected} onClose={() => setPromoteOpen(false)} onSubmit={submitPromote} loading={saving} /></>;
}
