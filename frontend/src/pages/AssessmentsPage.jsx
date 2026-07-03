import { Button, Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { listAssessments } from '../api/assessments';
import AppPageHeader from '../components/AppPageHeader';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import LoadingState from '../components/LoadingState';
import StatusChip from '../components/StatusChip';
import { apiErrorMessage } from '../utils/apiError';
import { formatDate } from '../utils/formatters';

export default function AssessmentsPage() {
  const [state, setState] = useState({ loading: true, error: '', assessments: [] });

  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try {
      const page = await listAssessments();
      setState({ loading: false, error: '', assessments: page.items });
    } catch (error) {
      setState({ loading: false, error: apiErrorMessage(error, 'Unable to load assessments.'), assessments: [] });
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <>
      <AppPageHeader title="Assessments" description="Authorised fictional assessment data for review and triage." />
      {state.loading ? <LoadingState label="Loading assessments" /> : null}
      {state.error ? <ErrorState message={state.error} onRetry={load} /> : null}
      {!state.loading && !state.error && state.assessments.length === 0 ? <EmptyState title="No assessments available" message="No authorised assessments are visible for this account." /> : null}
      {!state.loading && !state.error && state.assessments.length > 0 ? (
        <Card>
          <CardContent sx={{ p: 0 }}>
            <Table aria-label="Assessments table">
              <TableHead><TableRow><TableCell>Assessment name</TableCell><TableCell>Client</TableCell><TableCell>Framework</TableCell><TableCell>Status</TableCell><TableCell>Dates</TableCell><TableCell align="right">Open</TableCell></TableRow></TableHead>
              <TableBody>
                {state.assessments.map((assessment) => (
                  <TableRow key={assessment.id} hover tabIndex={0}>
                    <TableCell>{assessment.name}</TableCell>
                    <TableCell>Client #{assessment.client}</TableCell>
                    <TableCell>{assessment.framework}</TableCell>
                    <TableCell><StatusChip value={assessment.status} /></TableCell>
                    <TableCell>{formatDate(assessment.start_date)} - {formatDate(assessment.end_date)}</TableCell>
                    <TableCell align="right"><Button component={RouterLink} to={`/assessments/${assessment.id}`} size="small">Open</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </>
  );
}
