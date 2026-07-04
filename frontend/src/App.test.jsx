import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import ProtectedRoute from './auth/ProtectedRoute';
import AppShell from './layouts/AppShell';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import AssessmentsPage from './pages/AssessmentsPage';
import { ObservationsTable } from './features/assessments/ObservationsTab';
import ObservationDetailDrawer from './features/observations/ObservationDetailDrawer';
import ObservationTriageDialog from './features/observations/ObservationTriageDialog';
import FindingDetail from './features/findings/FindingDetail';
import { renderWithProviders } from './test/renderWithProviders';
import { listAssessments } from './api/assessments';
import { getDashboardSummary } from './api/dashboard';
import { getFinding } from './api/findings';
import { listAuditLogs } from './api/audit';
import { getFindingIntelligence, refreshFindingIntelligence } from './api/intelligence';
import { generateRemediationDraft, listAIArtifacts } from './api/ai';

vi.mock('./api/assessments', () => ({ listAssessments: vi.fn() }));
vi.mock('./api/dashboard', () => ({ getDashboardSummary: vi.fn() }));
vi.mock('./api/findings', () => ({ getFinding: vi.fn(), updateFinding: vi.fn() }));
vi.mock('./api/audit', () => ({ listAuditLogs: vi.fn() }));
vi.mock('./api/intelligence', () => ({ getFindingIntelligence: vi.fn(), refreshFindingIntelligence: vi.fn() }));
vi.mock('./api/ai', () => ({ generateRemediationDraft: vi.fn(), listAIArtifacts: vi.fn() }));

function auth(overrides = {}) {
  return {
    user: { email: 'consultant@example.test', role: 'CONSULTANT' },
    isAuthenticated: true,
    ready: true,
    login: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  };
}

test('login page renders email password fields and sign-in action', () => {
  renderWithProviders(<LoginPage />, { authValue: auth({ isAuthenticated: false, user: null }) });
  expect(screen.getByRole('heading', { name: 'SARP' })).toBeInTheDocument();
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
});

test('invalid login displays a generic error', async () => {
  const user = userEvent.setup();
  const login = vi.fn().mockRejectedValue(new Error('bad credentials'));
  renderWithProviders(<LoginPage />, { authValue: auth({ isAuthenticated: false, user: null, login }) });
  await user.type(screen.getByLabelText(/email/i), 'consultant@example.test');
  await user.type(screen.getByLabelText(/^password/i), 'wrong');
  await user.click(screen.getByRole('button', { name: /sign in/i }));
  expect(await screen.findByText(/unable to sign in/i)).toBeInTheDocument();
});

test('protected route redirects to login without authenticated state', () => {
  renderWithProviders(
    <Routes>
      <Route element={<ProtectedRoute />}><Route path="/assessments" element={<div>Protected</div>} /></Route>
      <Route path="/login" element={<div>Login route</div>} />
    </Routes>,
    { route: '/assessments', authValue: auth({ isAuthenticated: false, user: null }) },
  );
  expect(screen.getByText('Login route')).toBeInTheDocument();
});


test('dashboard displays management metrics from the API', async () => {
  getDashboardSummary.mockResolvedValue({
    open_findings: 3,
    critical_high_findings: 2,
    overdue_remediation: 1,
    findings_by_severity: { HIGH: 2, LOW: 1 },
    findings_by_scanner_source: { ZAP: 1, NESSUS: 1 },
    recent_imports: [],
  });
  renderWithProviders(<DashboardPage />);
  expect(await screen.findByText('Open findings')).toBeInTheDocument();
  expect(screen.getByText('3')).toBeInTheDocument();
  expect(screen.getByText('Critical/high findings')).toBeInTheDocument();
  expect(screen.getByText('Overdue remediation')).toBeInTheDocument();
});

test('assessment list displays API data', async () => {
  listAssessments.mockResolvedValue({ items: [{ id: 1, client: 7, name: 'Northwind Review', framework: 'OWASP', status: 'ACTIVE', start_date: '2026-07-01', end_date: null }], count: 1 });
  renderWithProviders(<AssessmentsPage />);
  expect(await screen.findByText('Northwind Review')).toBeInTheDocument();
  expect(screen.getByText('Client #7')).toBeInTheDocument();
});

test('assessment list renders an empty state', async () => {
  listAssessments.mockResolvedValue({ items: [], count: 0 });
  renderWithProviders(<AssessmentsPage />);
  expect(await screen.findByText(/no assessments available/i)).toBeInTheDocument();
});

test('observation table renders source and status chips', () => {
  renderWithProviders(<ObservationsTable observations={[{ id: 1, title: 'Missing header', source_tool: 'ZAP', raw_location: '/account', raw_severity: 'HIGH', triage_status: 'NEW', confidence: 'Medium', last_seen_at: '2026-07-01T10:00:00Z' }]} onOpen={vi.fn()} />);
  expect(screen.getByText('ZAP')).toBeInTheDocument();
  expect(screen.getByText('New')).toBeInTheDocument();
});

test('promote action is disabled until observation is confirmed', () => {
  renderWithProviders(<ObservationDetailDrawer open observation={{ id: 1, title: 'Open port', source_tool: 'NMAP', raw_severity: 'LOW', triage_status: 'NEW', cve_ids: [], cwe_ids: [] }} role="CONSULTANT" onClose={vi.fn()} onTriage={vi.fn()} onPromote={vi.fn()} />);
  expect(screen.getByRole('button', { name: /promote/i })).toBeDisabled();
});

test('triage dialog requires a note for false positive', async () => {
  const user = userEvent.setup();
  renderWithProviders(<ObservationTriageDialog open observation={{ id: 1, title: 'Observation' }} observations={[]} onClose={vi.fn()} onSubmit={vi.fn()} loading={false} />);
  await user.click(screen.getByLabelText(/triage action/i));
  await user.click(screen.getByRole('option', { name: /mark false positive/i }));
  await user.click(screen.getByRole('button', { name: /submit/i }));
  expect(await screen.findByText(/requires a note/i)).toBeInTheDocument();
});

test('app shell hides raw observation navigation for a client role', () => {
  renderWithProviders(<Routes><Route element={<AppShell />}><Route path="/" element={<div>Home</div>} /></Route></Routes>, { authValue: auth({ user: { email: 'client@example.test', role: 'CLIENT' } }) });
  expect(screen.getAllByText('Assessments').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
  expect(screen.queryByText('Scanner Observations')).not.toBeInTheDocument();
});


const findingPayload = {
  id: 42,
  assessment: 7,
  affected_asset: 3,
  title: 'Access control bypass',
  description: 'Fictional BOLA issue.',
  cve_id: 'CVE-2024-1234',
  cvss_score: '8.8',
  severity: 'HIGH',
  status: 'OPEN',
  due_date: '2026-08-01',
  business_impact: 'Fictional impact.',
  remediation: 'Fix authorization checks.',
  remediation_owner: 'Platform Team',
  priority_score: 98,
  priority_label: 'URGENT',
  priority_reason: 'Urgent because the finding has a high CVSS score and CISA KEV listing.',
  created_at: '2026-07-04T10:00:00Z',
};

function prepareFindingDetailMocks() {
  getFinding.mockResolvedValue(findingPayload);
  listAuditLogs.mockResolvedValue({ items: [] });
  getFindingIntelligence.mockResolvedValue({
    finding: findingPayload,
    intelligence: {
      cve_id: 'CVE-2024-1234',
      nvd_cvss_score: '8.8',
      kev_listed: true,
      epss_score: '0.7400',
      epss_percentile: '0.9600',
      source_retrieved_at: '2026-07-04T10:00:00Z',
    },
    used_cache: false,
  });
  listAIArtifacts.mockResolvedValue([{
    id: 9,
    content: 'Draft — human review required\n\nExecutive summary\nReview the access control issue.',
    sources: [{ rank: 1, title: 'Access-control remediation guidance', source_name: 'OWASP Cheat Sheet Series', source_url: 'https://cheatsheetseries.owasp.org/' }],
  }]);
}

test('finding detail renders CVE intelligence and refreshes cached priority', async () => {
  const user = userEvent.setup();
  prepareFindingDetailMocks();
  refreshFindingIntelligence.mockResolvedValue({ finding: { ...findingPayload, priority_score: 99 }, intelligence: { cve_id: 'CVE-2024-1234', kev_listed: true, nvd_cvss_score: '8.8' }, used_cache: false });

  renderWithProviders(<Routes><Route path="/findings/:findingId" element={<FindingDetail />} /></Routes>, { route: '/findings/42' });

  expect(await screen.findByText('CVE intelligence')).toBeInTheDocument();
  expect(screen.getByText('CVE-2024-1234')).toBeInTheDocument();
  expect(screen.getByText(/URGENT 98/)).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /refresh intelligence/i }));
  expect(await screen.findByText(/intelligence refreshed/i)).toBeInTheDocument();
});

test('finding detail renders remediation draft sources and generate action', async () => {
  const user = userEvent.setup();
  prepareFindingDetailMocks();
  generateRemediationDraft.mockResolvedValue({
    id: 10,
    content: 'Draft — human review required\n\nExecutive summary\nGenerated draft.',
    sources: [{ rank: 1, title: 'Vulnerability validation guidance', source_name: 'NIST', source_url: 'https://csrc.nist.gov/' }],
  });

  renderWithProviders(<Routes><Route path="/findings/:findingId" element={<FindingDetail />} /></Routes>, { route: '/findings/42' });

  expect(await screen.findByText('AI-assisted remediation')).toBeInTheDocument();
  expect(screen.getAllByText(/draft — human review required/i).length).toBeGreaterThan(0);
  expect(screen.getByText('Access-control remediation guidance')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /generate draft/i }));
  expect(await screen.findByText(/remediation draft generated/i)).toBeInTheDocument();
  expect(screen.getByText('Vulnerability validation guidance')).toBeInTheDocument();
});
