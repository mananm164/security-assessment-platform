import UploadFileIcon from '@mui/icons-material/UploadFile';
import { Alert, Box, Button, Card, CardContent, Snackbar, Stack, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useEffect, useState } from 'react';
import { listImports } from '../../api/imports';
import { useAuth } from '../../auth/AuthContext';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import SourceToolChip from '../../components/SourceToolChip';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDateTime } from '../../utils/formatters';
import { canWriteTechnicalRecords } from '../../utils/roleNavigation';
import ImportScanReportDialog from './ImportScanReportDialog';

export default function ImportsTab({ assessmentId, onOpenObservations }) {
  const { user } = useAuth();
  const canImport = canWriteTechnicalRecords(user?.role);
  const [state, setState] = useState({ loading: true, error: '', imports: [] });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [notice, setNotice] = useState('');

  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try {
      const page = await listImports();
      setState({ loading: false, error: '', imports: page.items.filter((item) => String(item.assessment) === String(assessmentId)) });
    } catch (error) {
      setState({ loading: false, error: apiErrorMessage(error, 'Unable to load imports.'), imports: [] });
    }
  }

  async function handleConfirmed(result) {
    await load();
    setNotice(`Import completed. Created ${result.observations_created} and re-observed ${result.observations_reobserved} observations.`);
    onOpenObservations?.();
  }

  useEffect(() => { load(); }, [assessmentId]);

  if (state.loading) return <LoadingState label="Loading imports" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;

  return (
    <>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2, alignItems: { xs: 'stretch', sm: 'center' }, justifyContent: 'space-between' }}>
        <Alert severity="info" sx={{ flex: 1 }}>Only upload reports for systems you are authorised to assess. SARP does not run scans.</Alert>
        {canImport ? (
          <Button variant="contained" startIcon={<UploadFileIcon />} onClick={() => setDialogOpen(true)}>
            Import scan report
          </Button>
        ) : null}
      </Stack>
      {!state.imports.length ? (
        <EmptyState title="No imports recorded" message={canImport ? 'Upload an authorised scanner export to add observations.' : 'No scanner imports have been confirmed for this assessment.'} />
      ) : (
        <Card>
          <CardContent sx={{ p: 0 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Imported at</TableCell>
                  <TableCell>Tool</TableCell>
                  <TableCell>Filename</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Re-observed</TableCell>
                  <TableCell align="right">Open observations</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {state.imports.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{formatDateTime(item.created_at)}</TableCell>
                    <TableCell><SourceToolChip value={item.source_tool} /></TableCell>
                    <TableCell>{item.source_filename}</TableCell>
                    <TableCell><StatusChip value={item.status} /></TableCell>
                    <TableCell>{item.observations_created}</TableCell>
                    <TableCell>{item.observations_updated}</TableCell>
                    <TableCell align="right"><Button size="small" onClick={onOpenObservations}>Open</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
      {canImport ? (
        <ImportScanReportDialog
          open={dialogOpen}
          assessmentId={assessmentId}
          onClose={() => setDialogOpen(false)}
          onConfirmed={handleConfirmed}
        />
      ) : null}
      <Snackbar open={Boolean(notice)} autoHideDuration={5000} onClose={() => setNotice('')} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Box><Alert severity="success" onClose={() => setNotice('')}>{notice}</Alert></Box>
      </Snackbar>
    </>
  );
}
