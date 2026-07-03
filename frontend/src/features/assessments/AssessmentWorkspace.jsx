import { Box, Card, CardContent, Chip, Link, Tab, Tabs, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink, useParams, useSearchParams } from 'react-router-dom';
import { getAssessment } from '../../api/assessments';
import { useAuth } from '../../auth/AuthContext';
import AppPageHeader from '../../components/AppPageHeader';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import StatusChip from '../../components/StatusChip';
import { apiErrorMessage } from '../../utils/apiError';
import { formatDate } from '../../utils/formatters';
import { canSeeRawScannerData } from '../../utils/roleNavigation';
import AssetsTab from './AssetsTab';
import AssessmentOverviewTab from './AssessmentOverviewTab';
import FindingsTab from './FindingsTab';
import ImportsTab from './ImportsTab';
import ObservationsTab from './ObservationsTab';

const tabLabels = {
  overview: 'Overview', assets: 'Assets', imports: 'Imports', observations: 'Scanner Observations', findings: 'Findings',
};

export default function AssessmentWorkspace() {
  const { assessmentId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const [state, setState] = useState({ loading: true, error: '', assessment: null });
  const canSeeRaw = canSeeRawScannerData(user?.role);
  const visibleTabs = ['overview', 'assets', ...(canSeeRaw ? ['imports', 'observations'] : []), 'findings'];
  const currentTab = visibleTabs.includes(searchParams.get('tab')) ? searchParams.get('tab') : 'overview';

  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try {
      const assessment = await getAssessment(assessmentId);
      setState({ loading: false, error: '', assessment });
    } catch (error) {
      setState({ loading: false, error: apiErrorMessage(error, 'Unable to load assessment.'), assessment: null });
    }
  }

  useEffect(() => { load(); }, [assessmentId]);

  if (state.loading) return <LoadingState label="Loading assessment" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;

  const { assessment } = state;
  return (
    <>
      <AppPageHeader
        title={`Assessment: ${assessment.name}`}
        description="Review imported observations before promoting confirmed issues to managed findings."
        breadcrumbs={<Link component={RouterLink} to="/assessments" underline="hover">Assessments</Link>}
      />
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">Client #{assessment.client}</Typography>
          <Chip size="small" label={assessment.framework} variant="outlined" />
          <StatusChip value={assessment.status} />
          <Typography variant="body2" color="text.secondary">{formatDate(assessment.start_date)} - {formatDate(assessment.end_date)}</Typography>
        </CardContent>
      </Card>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(_, value) => setSearchParams({ tab: value })} variant="scrollable" scrollButtons="auto">
          {visibleTabs.map((tab) => <Tab key={tab} value={tab} label={tabLabels[tab]} />)}
        </Tabs>
      </Box>
      {currentTab === 'overview' ? <AssessmentOverviewTab assessment={assessment} /> : null}
      {currentTab === 'assets' ? <AssetsTab assessmentId={assessment.id} /> : null}
      {currentTab === 'imports' ? <ImportsTab assessmentId={assessment.id} onOpenObservations={() => setSearchParams({ tab: 'observations' })} /> : null}
      {currentTab === 'observations' ? <ObservationsTab assessmentId={assessment.id} /> : null}
      {currentTab === 'findings' ? <FindingsTab assessmentId={assessment.id} /> : null}
    </>
  );
}
