import { Alert, Button, Stack } from '@mui/material';

export default function ErrorState({ message = 'Unable to load this view.', onRetry }) {
  return (
    <Stack spacing={2} sx={{ my: 2 }}>
      <Alert severity="error">{message}</Alert>
      {onRetry ? <Button variant="outlined" onClick={onRetry} sx={{ alignSelf: 'flex-start' }}>Retry</Button> : null}
    </Stack>
  );
}
