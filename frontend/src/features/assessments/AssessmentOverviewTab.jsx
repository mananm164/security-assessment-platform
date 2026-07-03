import { Card, CardContent, Stack, Typography } from '@mui/material';
import { formatDate } from '../../utils/formatters';

export default function AssessmentOverviewTab({ assessment }) {
  return (
    <Stack spacing={2}>
      <Card><CardContent><Typography variant="h6">Scope summary</Typography><Typography sx={{ mt: 1 }}>{assessment.scope_summary || 'No scope summary recorded.'}</Typography></CardContent></Card>
      <Card><CardContent><Typography variant="h6">Assessment facts</Typography><Typography color="text.secondary" sx={{ mt: 1 }}>Framework: {assessment.framework}</Typography><Typography color="text.secondary">Dates: {formatDate(assessment.start_date)} - {formatDate(assessment.end_date)}</Typography><Typography color="text.secondary">Imported observations require consultant review before they become Findings.</Typography></CardContent></Card>
    </Stack>
  );
}
