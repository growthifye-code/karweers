import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import Home from "@/pages/Home";
import InsightsPage from "@/pages/InsightsPage";
import ArticleDetail from "@/pages/ArticleDetail";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import AdminDashboard from "@/pages/AdminDashboard";
import ClientDashboard from "@/pages/ClientDashboard";
import PaymentSuccess from "@/pages/PaymentSuccess";
import PaymentCancel from "@/pages/PaymentCancel";
import ProtectedRoute from "@/components/ProtectedRoute";
import AIChatWidget from "@/components/AIChatWidget";

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/insights" element={<InsightsPage />} />
            <Route path="/insights/:slug" element={<ArticleDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<ProtectedRoute><ClientDashboard /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute admin><AdminDashboard /></ProtectedRoute>} />
            <Route path="/payment/success" element={<PaymentSuccess />} />
            <Route path="/payment/cancel" element={<PaymentCancel />} />
          </Routes>
          <AIChatWidget />
          <Toaster position="top-center" richColors />
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
