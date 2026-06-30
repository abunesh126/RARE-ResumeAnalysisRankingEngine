import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import DashboardPage from '../pages/Dashboard';
import CandidatesPage from '../pages/Candidates';
import AnalyticsPage from '../pages/Analytics';
import ResumeLibraryPage from '../pages/ResumeLibrary';
import TemplatesPage from '../pages/Templates';
import HistoryPage from '../pages/History';
import ReportsPage from '../pages/Reports';
import SettingsPage from '../pages/Settings';
import SupportPage from '../pages/Support';
import ActiveRankingsPage from '../pages/ActiveRankings';

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'candidates', element: <CandidatesPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'library', element: <ResumeLibraryPage /> },
      { path: 'templates', element: <TemplatesPage /> },
      { path: 'history', element: <HistoryPage /> },
      { path: 'rankings', element: <ActiveRankingsPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'support', element: <SupportPage /> },
    ],
  },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
