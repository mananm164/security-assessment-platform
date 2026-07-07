import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { beforeEach, vi } from 'vitest';
import ProtectedRoute from './auth/ProtectedRoute';
import AppShell from './layouts/AppShell';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import AssessmentsPage from './pages/AssessmentsPage';
import ImportsTab from './features/assessments/ImportsTab';
import { ObservationsTable } from './features/assessments/ObservationsTab';
import ObservationDetailDrawer from './features/observations/ObservationDetailDrawer';
import ObservationTriageDialog from './features/observations/ObservationTriageDialog';
import FindingDetail from './features/findings/FindingDetail';
import FindingUpdateDialog from './features/findings/FindingUpdateDialog';
import AuditTimeline from './features/findings/AuditTimeline';
import { renderWithProviders } from './test/renderWithProviders';
import { listAssessments } from './api/assessments';
import { getDashboardSummary } from './api/dashboard';
import { getFinding, listFindingAuditLogs, updateFinding } from './api/findings';
import { listAuditLogs } from './api/audit';
import { getFindingIntelligence, refreshFindingIntelligence } from './api/intelligence';
import { generateRemediationDraft, listAIArtifacts } from './api/ai';
import { confirmImportPreview, createImportPreview, listImports } from './api/imports';

vi.mock('./api/assessments', () => ({ listAssessments: vi.fn() }));
vi.mock('./api/dashboard', () => ({ getDashboardSummary: vi.fn() }));
vi.mock('./api/findings', () => ({ getFinding: vi.fn(), updateFinding: vi.fn(), listFindingAuditLogs: vi.fn() }));
vi.mock('./api/audit', () => ({ listAuditLogs: vi.fn() }));
vi.mock('./api/intelligence', () => ({ getFindingIntelligence: vi.fn(), refreshFindingIntelligence: vi.fn() }));
vi.mock('./api/ai', () => ({ generateRemediationDraft: vi.fn(), listAIArtifacts: vi.fn() }));
vi.mock('./api/imports', () => ({ listImports: vi.fn(), createImportPreview: vi.fn(), confirmImportPreview: vi.fn() }));

beforeEach(() => {
  vi.clearAllMocks();
});

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
    metrics: { open_findings: 3, critical_high_findings: 2, overdue_remediations: 1, recent_imports: 0 },
    severity_distribution: [{ severity: 'HIGH', count: 2 }, { severity: 'LOW', count: 1 }],
    status_distribution: [{ status: 'OPEN', count: 3 }],
    source_distribution: [{ source_tool: 'ZAP', finding_count: 1 }, { source_tool: 'NESSUS', finding_count: 1 }],
    top_priority_findings: [],
    recent_imports: [],
    recent_activity: [],
  });
  renderWithProviders(<DashboardPage />);
  expect(await screen.findByText('Open findings')).toBeInTheDocument();
  expect(screen.getAllByText('3').length).toBeGreaterThan(0);
  expect(screen.getByText('Critical / High')).toBeInTheDocument();
  expect(screen.getByText('Overdue')).toBeInTheDocument();
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
  updateFinding.mockResolvedValue(findingPayload);
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
  listFindingAuditLogs.mockResolvedValue({ items: [] });
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


test('dashboard displays a safe error state', async () => {
  getDashboardSummary.mockRejectedValue({ response: { status: 500 } });
  renderWithProviders(<DashboardPage />);
  expect(await screen.findByText(/service is unavailable/i)).toBeInTheDocument();
});

test('client dashboard response omits recent imports card', async () => {
  getDashboardSummary.mockResolvedValue({
    metrics: { open_findings: 1, critical_high_findings: 0, overdue_remediations: 0 },
    severity_distribution: [],
    status_distribution: [],
    source_distribution: [],
    top_priority_findings: [],
    recent_imports: [],
  });
  renderWithProviders(<DashboardPage />, { authValue: auth({ user: { email: 'client@example.test', role: 'CLIENT' } }) });
  expect(await screen.findByText('Risk Dashboard')).toBeInTheDocument();
  expect(screen.queryByText('Recent imports')).not.toBeInTheDocument();
});

test('lifecycle dialog sends remediation patch payload', async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  renderWithProviders(<FindingUpdateDialog open finding={findingPayload} loading={false} onClose={vi.fn()} onSubmit={onSubmit} />);
  await user.clear(screen.getByLabelText(/remediation owner/i));
  await user.type(screen.getByLabelText(/remediation owner/i), 'Platform Team');
  await user.click(screen.getByRole('button', { name: /^save$/i }));
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ remediation_owner: 'Platform Team', status: 'OPEN' }));
});

test('accepted-risk lifecycle form requires reason and review date', async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  renderWithProviders(<FindingUpdateDialog open finding={{ ...findingPayload, status: 'ACCEPTED_RISK' }} loading={false} onClose={vi.fn()} onSubmit={onSubmit} />);
  await user.clear(screen.getByLabelText(/accepted-risk reason/i));
  await user.click(screen.getByRole('button', { name: /^save$/i }));
  expect(await screen.findByText(/accepted risk requires/i)).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});

test('lifecycle dialog displays backend validation error safely', () => {
  renderWithProviders(<FindingUpdateDialog open finding={findingPayload} loading={false} submitError="Validation evidence is required before closing a finding." onClose={vi.fn()} onSubmit={vi.fn()} />);
  expect(screen.getByText(/validation evidence is required/i)).toBeInTheDocument();
});

test('audit timeline renders readable safe activity', () => {
  renderWithProviders(<AuditTimeline logs={[{ id: 1, action: 'FINDING_STATUS_CHANGED', actor: { id: 2, email: 'consultant@example.test' }, safe_metadata: { old_status: 'OPEN', new_status: 'IN_PROGRESS' }, created_at: '2026-07-06T10:00:00Z' }]} />);
  expect(screen.getAllByText(/status changed/i).length).toBeGreaterThan(0);
  expect(screen.queryByText(/old_status/)).not.toBeInTheDocument();
});

test('finding detail surfaces close validation error from backend', async () => {
  const user = userEvent.setup();
  prepareFindingDetailMocks();
  updateFinding.mockRejectedValue({ response: { status: 400, data: { validation_evidence: ['Validation evidence is required before closing a finding.'] } } });
  renderWithProviders(<Routes><Route path="/findings/:findingId" element={<FindingDetail />} /></Routes>, { route: '/findings/42' });
  await screen.findByText('CVE intelligence');
  await user.click(screen.getByRole('button', { name: /update finding/i }));
  await user.click(screen.getByRole('button', { name: /^save$/i }));
  expect((await screen.findAllByText(/validation evidence is required/i)).length).toBeGreaterThan(0);
});


test('browser import button is visible only for write roles', async () => {
  listImports.mockResolvedValue({ items: [], count: 0 });

  const first = renderWithProviders(<ImportsTab assessmentId={7} onOpenObservations={vi.fn()} />);
  expect(await screen.findByRole('button', { name: /import scan report/i })).toBeInTheDocument();
  first.unmount();

  listImports.mockResolvedValue({ items: [], count: 0 });
  renderWithProviders(<ImportsTab assessmentId={7} onOpenObservations={vi.fn()} />, { authValue: auth({ user: { email: 'manager@example.test', role: 'MANAGER' } }) });
  expect(await screen.findByText(/no scanner imports have been confirmed/i)).toBeInTheDocument();
  expect(screen.getByText(/only upload reports/i)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /import scan report/i })).not.toBeInTheDocument();
});

test('browser import dialog previews and confirms a safe report', async () => {
  const user = userEvent.setup();
  const onOpenObservations = vi.fn();
  listImports.mockResolvedValue({ items: [], count: 0 });
  createImportPreview.mockResolvedValue({
    id: 55,
    assessment: 7,
    source_tool: 'ZAP',
    source_filename: 'zap-report.json',
    file_size_bytes: 18234,
    summary: { total_observations: 1, assets_detected: 1, source_tool: 'ZAP' },
    observations: [{ title: 'Missing Anti-clickjacking Header', raw_severity: 'Medium', asset_label: 'https://training-app.local', location: '/account', confidence: 'Medium' }],
  });
  confirmImportPreview.mockResolvedValue({ scan_import_id: 44, assessment: 7, source_tool: 'ZAP', observations_created: 1, observations_reobserved: 0 });

  renderWithProviders(<ImportsTab assessmentId={7} onOpenObservations={onOpenObservations} />);
  await user.click(await screen.findByRole('button', { name: /import scan report/i }));
  expect(screen.getByRole('button', { name: /generate preview/i })).toBeDisabled();

  const file = new File(['{"site":[{}]}'], 'zap-report.json', { type: 'application/json' });
  await user.upload(document.querySelector('input[type="file"]'), file);
  await user.click(screen.getByRole('button', { name: /generate preview/i }));

  expect(createImportPreview).toHaveBeenCalledWith(7, { sourceTool: 'zap', file });
  expect(await screen.findByText('Missing Anti-clickjacking Header')).toBeInTheDocument();
  expect(screen.queryByText(/requestresponse/i)).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: /confirm import/i }));
  expect(confirmImportPreview).toHaveBeenCalledWith(55);
  expect((await screen.findAllByText(/created 1 and re-observed 0/i)).length).toBeGreaterThan(0);
  expect(onOpenObservations).toHaveBeenCalled();
  expect(listImports).toHaveBeenCalledTimes(2);
});

test('browser import dialog displays expired preview errors safely', async () => {
  const user = userEvent.setup();
  listImports.mockResolvedValue({ items: [], count: 0 });
  createImportPreview.mockResolvedValue({
    id: 56,
    assessment: 7,
    source_tool: 'NMAP',
    source_filename: 'sample.xml',
    file_size_bytes: 100,
    summary: { total_observations: 1, assets_detected: 1, source_tool: 'NMAP' },
    observations: [{ title: 'Open SSH port', raw_severity: 'Info', asset_label: '10.0.0.5', location: 'tcp/22', confidence: '' }],
  });
  confirmImportPreview.mockRejectedValue({ response: { status: 410, data: { detail: 'This import preview has expired. Upload the report again to continue.' } } });

  renderWithProviders(<ImportsTab assessmentId={7} onOpenObservations={vi.fn()} />);
  await user.click(await screen.findByRole('button', { name: /import scan report/i }));
  await user.click(screen.getByLabelText(/source tool/i));
  await user.click(screen.getByRole('option', { name: /nmap/i }));
  await user.upload(document.querySelector('input[type="file"]'), new File(['<nmaprun />'], 'sample.xml', { type: 'text/xml' }));
  await user.click(screen.getByRole('button', { name: /generate preview/i }));
  await screen.findByText('Open SSH port');
  await user.click(screen.getByRole('button', { name: /confirm import/i }));

  expect(await screen.findByText(/preview has expired/i)).toBeInTheDocument();
  expect(screen.queryByText(/<nmaprun/i)).not.toBeInTheDocument();
});
