import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from '../auth/ProtectedRoute';
import AppShell from '../layouts/AppShell';
import AssessmentDetailPage from '../pages/AssessmentDetailPage';
import DashboardPage from '../pages/DashboardPage';
import AssessmentsPage from '../pages/AssessmentsPage';
import FindingDetailPage from '../pages/FindingDetailPage';
import LoginPage from '../pages/LoginPage';
import NotFoundPage from '../pages/NotFoundPage';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/assessments" element={<AssessmentsPage />} />
          <Route path="/assessments/:assessmentId" element={<AssessmentDetailPage />} />
          <Route path="/findings/:findingId" element={<FindingDetailPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
