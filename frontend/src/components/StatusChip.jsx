import { Chip } from '@mui/material';
import { titleCase } from '../utils/formatters';

const colors = { CONFIRMED: 'info', FALSE_POSITIVE: 'default', DUPLICATE: 'secondary', PROMOTED: 'success', NEW: 'default', OPEN: 'default', IN_PROGRESS: 'info', VALIDATION_PENDING: 'warning', MITIGATED: 'success', CLOSED: 'success', ACCEPTED_RISK: 'secondary' };

export default function StatusChip({ value }) {
  return <Chip size="small" label={titleCase(value)} color={colors[value] || 'default'} variant={value === 'NEW' || value === 'FALSE_POSITIVE' ? 'outlined' : 'filled'} />;
}
