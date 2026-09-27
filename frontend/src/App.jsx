import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import CaseDetail from "./pages/CaseDetail.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-soc-bg">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cases/:id" element={<CaseDetail />} />
      </Routes>
    </div>
  );
}
