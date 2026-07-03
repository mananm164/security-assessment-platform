import { Chip } from '@mui/material';

const labels = { NMAP: 'Nmap', ZAP: 'ZAP', NESSUS: 'Nessus', BURP: 'Burp' };

export default function SourceToolChip({ value }) {
  return <Chip size="small" label={labels[value] || value || 'Unknown'} variant="outlined" />;
}
