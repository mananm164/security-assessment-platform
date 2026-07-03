import { Button, Card, CardContent, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <Card>
      <CardContent>
        <Typography variant="h5">Page not found</Typography>
        <Typography color="text.secondary" sx={{ mt: 1, mb: 2 }}>The requested page is not available.</Typography>
        <Button component={RouterLink} to="/assessments" variant="contained">Back to assessments</Button>
      </CardContent>
    </Card>
  );
}
