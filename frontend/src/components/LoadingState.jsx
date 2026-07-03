import { Box, CircularProgress, Typography } from '@mui/material';

export default function LoadingState({ label = 'Loading records' }) {
  return (
    <Box aria-live="polite" sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 3 }}>
      <CircularProgress size={24} />
      <Typography color="text.secondary">{label}</Typography>
    </Box>
  );
}
