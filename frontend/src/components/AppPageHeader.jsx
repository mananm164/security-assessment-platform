import { Box, Breadcrumbs, Typography } from '@mui/material';

export default function AppPageHeader({ title, description, breadcrumbs, action }) {
  return (
    <Box sx={{ mb: 3 }}>
      {breadcrumbs ? <Breadcrumbs sx={{ mb: 1 }}>{breadcrumbs}</Breadcrumbs> : null}
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 2 }}>
        <Box>
          <Typography variant="h5" component="h1">{title}</Typography>
          {description ? <Typography color="text.secondary" sx={{ mt: 0.5 }}>{description}</Typography> : null}
        </Box>
        {action}
      </Box>
    </Box>
  );
}
