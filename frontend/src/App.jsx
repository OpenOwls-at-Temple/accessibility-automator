import { Route, Routes } from "react-router-dom";
import AdminUsers from "./pages/AdminUsers.jsx";
import HomePage from "./pages/HomePage.jsx";
import ReportPage from "./pages/ReportPage.jsx";
import Settings from "./pages/Settings.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/admin" element={<AdminUsers />} />
      <Route path="/groups/:group/files/:name/report" element={<ReportPage />} />
    </Routes>
  );
}
