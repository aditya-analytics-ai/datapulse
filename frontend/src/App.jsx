import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import WelcomePage from './pages/WelcomePage';
import LoginPage from './pages/LoginPage';
import GoogleCallbackPage from './pages/GoogleCallbackPage';
import ScraperPage from './pages/ScraperPage';
import HistoryPage from './pages/HistoryPage';
import JobMarketPage from './pages/JobMarketPage';
import PriceTrackerPage from './pages/PriceTrackerPage';
import './styles/global.css';
import './styles/animations.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"       element={<WelcomePage />} />
        <Route path="/login"  element={<LoginPage />} />
        <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
        <Route path="/app"    element={<Layout />}>
          <Route index         element={<Navigate to="/app/scraper" replace />} />
          <Route path="scraper" element={<ScraperPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="jobs"    element={<JobMarketPage />} />
          <Route path="tracker" element={<PriceTrackerPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
