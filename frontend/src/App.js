import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import Home from "@/pages/Home";
import AboutPage from "@/pages/AboutPage";
import ServicesIndex from "@/pages/ServicesIndex";
import ServicePage from "@/pages/ServicePage";
import LegalPage from "@/pages/LegalPage";
import CaseStudiesPage from "@/pages/CaseStudiesPage";
import MarketPage from "@/pages/MarketPage";
import DealsPage from "@/pages/DealsPage";
import InsightsPage from "@/pages/InsightsPage";
import ArticleDetail from "@/pages/ArticleDetail";
import LearningPage from "@/pages/LearningPage";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import AuthCallback from "@/pages/AuthCallback";
import AdminDashboard from "@/pages/AdminDashboard";
import ClientDashboard from "@/pages/ClientDashboard";
import BookingManage from "@/pages/BookingManage";
import ProtectedRoute from "@/components/ProtectedRoute";
import AIChatWidget from "@/components/AIChatWidget";
import ConsentBanner from "@/components/ConsentBanner";
import PageTracker from "@/components/PageTracker";
import VpnGate from "@/components/VpnGate";

function AppRoutes() {
  const location = useLocation();
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
      <Route path="/market" element={<MarketPage />} />
      <Route path="/deals" element={<DealsPage />} />
      <Route path="/learning" element={<LearningPage />} />
      <Route path="/insights/:slug" element={<ArticleDetail />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<ProtectedRoute><ClientDashboard /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute admin><AdminDashboard /></ProtectedRoute>} />
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
          <AIChatWidget />
          <ConsentBanner />
          <Toaster position="top-center" richColors />
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
