import { Routes, Route } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import Nav from "./components/Nav";
import DeepfakePage from "./pages/DeepfakePage";
import Home from "./pages/Home";
import AnalyzerPage from "./pages/AnalyzerPage";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

export default function App() {
  return (
    <AuthProvider>
      <div className="noise min-h-screen bg-cyber-black">
        <Nav />
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/analyze" element={<ProtectedRoute><AnalyzerPage /></ProtectedRoute>} />
            <Route path="/deepfake" element={<DeepfakePage />} />
          </Routes>
        </AnimatePresence>
      </div>
    </AuthProvider>
  );
}