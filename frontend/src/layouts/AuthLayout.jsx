import { Box, Container } from '@mui/material';

export default function AuthLayout({ children }) {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', display: 'flex', alignItems: 'center' }}>
      <Container maxWidth="sm">{children}</Container>
    </Box>
  );
}
