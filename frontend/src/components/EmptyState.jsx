import { Box, Typography } from '@mui/material';

export default function EmptyState({ title = 'No records found', message = 'There is nothing to show for the current view.' }) {
  return (
    <Box sx={{ p: 3, textAlign: 'center', border: '1px dashed', borderColor: 'divider', borderRadius: 2 }}>
      <Typography variant="h6">{title}</Typography>
      <Typography color="text.secondary" sx={{ mt: 0.5 }}>{message}</Typography>
    </Box>
  );
}
