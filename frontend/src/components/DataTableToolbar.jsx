import { Box, FormControl, InputLabel, MenuItem, Select } from '@mui/material';

export default function DataTableToolbar({ sourceTool, triageStatus, onSourceToolChange, onTriageStatusChange }) {
  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
      <FormControl size="small" sx={{ minWidth: 180 }}>
        <InputLabel id="source-tool-label">Source tool</InputLabel>
        <Select labelId="source-tool-label" label="Source tool" value={sourceTool} onChange={(event) => onSourceToolChange(event.target.value)}>
          <MenuItem value="">All</MenuItem>
          <MenuItem value="NMAP">Nmap</MenuItem>
          <MenuItem value="ZAP">ZAP</MenuItem>
          <MenuItem value="NESSUS">Nessus</MenuItem>
          <MenuItem value="BURP">Burp</MenuItem>
        </Select>
      </FormControl>
      <FormControl size="small" sx={{ minWidth: 180 }}>
        <InputLabel id="triage-status-label">Triage</InputLabel>
        <Select labelId="triage-status-label" label="Triage" value={triageStatus} onChange={(event) => onTriageStatusChange(event.target.value)}>
          <MenuItem value="">All</MenuItem>
          <MenuItem value="NEW">New</MenuItem>
          <MenuItem value="CONFIRMED">Confirmed</MenuItem>
          <MenuItem value="FALSE_POSITIVE">False positive</MenuItem>
          <MenuItem value="DUPLICATE">Duplicate</MenuItem>
          <MenuItem value="PROMOTED">Promoted</MenuItem>
        </Select>
      </FormControl>
    </Box>
  );
}
