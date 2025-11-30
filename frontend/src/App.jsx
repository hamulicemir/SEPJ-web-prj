import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing.jsx";
import AdminPage from "./pages/AdminPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/admin" element={<AdminPage />} />
    </Routes>
  );
}
