import { Chip } from '@mui/material';
import { titleCase } from '../utils/formatters';

const colors = { CONFIRMED: 'info', FALSE_POSITIVE: 'default', DUPLICATE: 'secondary', PROMOTED: 'success', NEW: 'default' };

export default function StatusChip({ value }) {
  return <Chip size="small" label={titleCase(value)} color={colors[value] || 'default'} variant={value === 'NEW' || value === 'FALSE_POSITIVE' ? 'outlined' : 'filled'} />;
}
