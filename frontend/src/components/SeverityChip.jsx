import { Chip } from '@mui/material';

const colors = { CRITICAL: 'error', HIGH: 'warning', MEDIUM: 'warning', LOW: 'info', INFORMATIONAL: 'default' };

export default function SeverityChip({ value }) {
  const label = value || 'Unknown';
  return <Chip size="small" label={label} color={colors[label] || 'default'} variant={label === 'LOW' ? 'outlined' : 'filled'} />;
}
