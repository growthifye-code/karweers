import "@/App.css";
import { useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import { getAdminPath, loadPublicConfig } from "@/config";
import Home from "@/pages/Home";
import AboutPage from "@/pages/AboutPage";
import ServicesIndex from "@/pages/ServicesIndex";
import ServicePage from "@/pages/ServicePage";
import LegalPage from "@/pages/LegalPage";
import CaseStudiesPage from "@/pages/CaseStudiesPage";
import ProductsPage from "@/pages/ProductsPage";
import StrategyToolkitPage from "@/pages/StrategyToolkitPage";
import StrategyInsightPage from "@/pages/StrategyInsightPage";
import ServiceInsightPage from "@/pages/ServiceInsightPage";
import InsightsHubPage from "@/pages/InsightsHubPage";
import ThemePage from "@/pages/ThemePage";
import ArchivePage from "@/pages/ArchivePage";
import CohortsPage from "@/pages/CohortsPage";
import CorporatePage from "@/pages/CorporatePage";
import MarketPage from "@/pages/MarketPage";
import DealsPage from "@/pages/DealsPage";
import InsightsPage from "@/pages/InsightsPage";
import ArticleDetail from "@/pages/ArticleDetail";
import LearningPage from "@/pages/LearningPage";
import SignalsArchivePage from "@/pages/SignalsArchivePage";
import ResumePaymentPage from "@/pages/ResumePaymentPage";
import ExplorePage from "@/pages/ExplorePage";
import EntityPage from "@/pages/EntityPage";
import PreferencesPage from "@/pages/PreferencesPage";
import LeadershipLabPage from "@/pages/LeadershipLabPage";
import LibraryPage from "@/pages/LibraryPage";
import BookPage from "@/pages/BookPage";
import GamesPage from "@/pages/GamesPage";
import GamePlayPage from "@/pages/GamePlayPage";
import GamesLeaderboardPage from "@/pages/GamesLeaderboardPage";
import AssessmentPage from "@/pages/AssessmentPage";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import PodcastPage from "@/pages/PodcastPage";
import AuthCallback from "@/pages/AuthCallback";
import AdminDashboard from "@/pages/AdminDashboard";
import ClientDashboard from "@/pages/ClientDashboard";
import BookingManage from "@/pages/BookingManage";
import ProtectedRoute from "@/components/ProtectedRoute";
import AIChatWidget from "@/components/AIChatWidget";
import StickyBookCTA from "@/components/StickyBookCTA";
import ConsentBanner from "@/components/ConsentBanner";
import PageTracker from "@/components/PageTracker";
import VpnGate from "@/components/VpnGate";

function AppRoutes() {
  const location = useLocation();
  // Load non-sensitive public config (reCAPTCHA sitekey) once at startup.
  useEffect(() => { loadPublicConfig(); }, []);
  const adminPath = getAdminPath();
  // Process Google OAuth callback FIRST (session_id in URL fragment).
  if (location.hash?.includes("session_id=")) return <AuthCallback />;
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/services" element={<ServicesIndex />} />
      <Route path="/services/:slug" element={<ServicePage />} />
      <Route path="/services/:slug/:phase" element={<ServicePage />} />
      <Route path="/privacy" element={<LegalPage doc="privacy" />} />
      <Route path="/terms" element={<LegalPage doc="terms" />} />
      <Route path="/refund" element={<LegalPage doc="refund" />} />
      <Route path="/insights" element={<InsightsPage />} />
      <Route path="/case-studies" element={<CaseStudiesPage />} />
      <Route path="/products" element={<ProductsPage />} />
      <Route path="/strategy-tools" element={<StrategyToolkitPage />} />
      <Route path="/strategy-insights/:slug" element={<StrategyInsightPage />} />
      <Route path="/insights-hub" element={<InsightsHubPage />} />
      <Route path="/insights/theme/:themeSlug" element={<ThemePage />} />
      <Route path="/insights-hub/archive" element={<ArchivePage />} />
      <Route path="/archive" element={<ArchivePage />} />
      <Route path="/archive/edition/:id" element={<ServiceInsightPage archived />} />
      <Route path="/insight/:slug" element={<ServiceInsightPage />} />
      <Route path="/cohorts" element={<CohortsPage />} />
      <Route path="/corporate" element={<CorporatePage />} />
      <Route path="/market" element={<MarketPage />} />
      <Route path="/deals" element={<DealsPage />} />
      <Route path="/learning" element={<LearningPage />} />
      <Route path="/podcast" element={<PodcastPage />} />
      <Route path="/explore" element={<ExplorePage />} />
      <Route path="/sectors/:slug" element={<EntityPage kind="sector" />} />
      <Route path="/capital/:slug" element={<EntityPage kind="agency" />} />
      <Route path="/oems/:slug" element={<EntityPage kind="oem" />} />
      <Route path="/preferences" element={<PreferencesPage />} />
      <Route path="/leadership-lab" element={<LeadershipLabPage />} />
      <Route path="/library" element={<LibraryPage />} />
      <Route path="/library/:slug" element={<BookPage />} />
      <Route path="/games" element={<GamesPage />} />
      <Route path="/games/:slug" element={<GamePlayPage />} />
      <Route path="/leaderboard" element={<GamesLeaderboardPage />} />
      <Route path="/assessment" element={<AssessmentPage />} />
      <Route path="/signals" element={<SignalsArchivePage />} />
      <Route path="/signals/:date" element={<SignalsArchivePage />} />
      <Route path="/resume/:bid" element={<ResumePaymentPage />} />
      <Route path="/insights/:slug" element={<ArticleDetail />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<ProtectedRoute><ClientDashboard /></ProtectedRoute>} />
      <Route path={adminPath} element={<ProtectedRoute admin><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin" element={<Navigate to="/login" replace />} />
      <Route path="/booking/manage" element={<BookingManage />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <PageTracker />
          <AppRoutes />
          <VpnGate />
          <StickyBookCTA />
          <AIChatWidget />
          <ConsentBanner />
          <Toaster position="top-center" richColors />
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
