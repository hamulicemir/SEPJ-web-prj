import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Report from "./pages/ReportGenerator";

function App() {
  return (
    <Router>
      <Navbar />
      <div className="p-4">
        <Routes>
          <Route path="/" element={<Report />} />
          <Route path="/ReportGenerator" element={<Report />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
