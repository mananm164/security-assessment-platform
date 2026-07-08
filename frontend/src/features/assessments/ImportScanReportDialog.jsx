import UploadFileIcon from '@mui/icons-material/UploadFile';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { confirmImportPreview, createImportPreview } from '../../api/imports';
import SourceToolChip from '../../components/SourceToolChip';
import { apiErrorMessage } from '../../utils/apiError';

const tools = [
  { value: 'nmap', label: 'Nmap', accept: '.xml' },
  { value: 'zap', label: 'OWASP ZAP', accept: '.json' },
  { value: 'nessus', label: 'Nessus', accept: '.nessus' },
  { value: 'burp', label: 'Burp Suite', accept: '.xml' },
];

function formatBytes(value) {
  if (!value) return '0 B';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ImportScanReportDialog({ open, assessmentId, onClose, onConfirmed }) {
  const [sourceTool, setSourceTool] = useState('zap');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const selectedTool = useMemo(() => tools.find((item) => item.value === sourceTool), [sourceTool]);

  useEffect(() => {
    if (!open) {
      setSourceTool('zap');
      setFile(null);
      setPreview(null);
      setResult(null);
      setLoading(false);
      setError('');
    }
  }, [open]);

  async function handlePreview() {
    if (!sourceTool || !file) {
      setError('Select a source tool and report file.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const nextPreview = await createImportPreview(assessmentId, { sourceTool, file });
      setPreview(nextPreview);
    } catch (apiError) {
      setError(apiErrorMessage(apiError, 'Unable to validate this report.'));
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm() {
    if (!preview) return;
    setLoading(true);
    setError('');
    try {
      const confirmation = await confirmImportPreview(preview.id);
      setResult(confirmation);
      await onConfirmed?.(confirmation);
    } catch (apiError) {
      setError(apiErrorMessage(apiError, 'Unable to confirm this import.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} fullWidth maxWidth="md">
      <DialogTitle>Import scan report</DialogTitle>
      {loading ? <LinearProgress /> : null}
      <DialogContent dividers>
        <Stack spacing={2}>
          <Alert severity="warning">Only upload reports for systems you are authorised to assess. SARP does not run scans.</Alert>
          {error ? <Alert severity="error">{error}</Alert> : null}
          {result ? (
            <Alert severity="success">
              Import completed. Created {result.observations_created} and re-observed {result.observations_reobserved} observations.
            </Alert>
          ) : null}
          {!preview ? (
            <Stack spacing={2}>
              <FormControl fullWidth>
                <InputLabel id="source-tool-label">Source tool</InputLabel>
                <Select
                  labelId="source-tool-label"
                  label="Source tool"
                  value={sourceTool}
                  onChange={(event) => { setSourceTool(event.target.value); setFile(null); }}
                >
                  {tools.map((tool) => <MenuItem key={tool.value} value={tool.value}>{tool.label}</MenuItem>)}
                </Select>
              </FormControl>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ alignItems: { xs: 'stretch', sm: 'center' } }}>
                <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
                  Choose report file
                  <input
                    hidden
                    type="file"
                    accept={selectedTool?.accept}
                    onChange={(event) => setFile(event.target.files?.[0] || null)}
                  />
                </Button>
                <Typography variant="body2" color="text.secondary">
                  {file ? `${file.name} (${formatBytes(file.size)})` : `Expected ${selectedTool?.accept || 'scanner export'} file`}
                </Typography>
              </Stack>
            </Stack>
          ) : (
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                <SourceToolChip value={preview.source_tool} />
                <Chip size="small" label={preview.source_filename} variant="outlined" />
                <Chip size="small" label={formatBytes(preview.file_size_bytes)} variant="outlined" />
              </Stack>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  {preview.summary?.total_observations || 0} observations across {preview.summary?.assets_detected || 0} detected assets. Preview expires in 15 minutes.
                </Typography>
              </Box>
              <Alert severity="info">
                Confirming will create or re-observe scanner observations in this assessment. Scanner results still require Consultant review before they become Findings.
              </Alert>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Observation</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Asset / location</TableCell>
                    <TableCell>Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(preview.observations || []).map((item, index) => (
                    <TableRow key={`${item.title}-${index}`}>
                      <TableCell>{item.title}</TableCell>
                      <TableCell><Chip size="small" label={item.raw_severity || 'Unknown'} variant="outlined" /></TableCell>
                      <TableCell>{[item.asset_label, item.location].filter(Boolean).join(' - ') || 'Not specified'}</TableCell>
                      <TableCell>{item.confidence || 'Not specified'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Stack>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        {preview && !result ? <Button onClick={() => { setPreview(null); setError(''); }} disabled={loading}>Back</Button> : null}
        <Button onClick={onClose} disabled={loading}>{result ? 'Close' : 'Cancel'}</Button>
        {!preview ? (
          <Button variant="contained" onClick={handlePreview} disabled={loading || !sourceTool || !file}>Generate preview</Button>
        ) : !result ? (
          <Button variant="contained" onClick={handleConfirm} disabled={loading}>Confirm import</Button>
        ) : null}
      </DialogActions>
    </Dialog>
  );
}
