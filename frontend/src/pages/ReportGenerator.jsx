import React, { useState } from "react";
import axios from "axios";
import DownloadButton from "../components/DownloadButton";
import Navbar from "../../../src/components/Navbar";

function ReportGenerator() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [analysisStatus, setAnalysisStatus] = useState("");
  const [result, setResult] = useState("");
  const [fileName, setFileName] = useState("");

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setUploadMessage("");
    setAnalysisStatus("");
    setResult("");
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(
        "http://localhost:3001/reports/upload",
        formData
      );
      setUploadMessage(`${selectedFile.name} wurde erfolgreich hochgeladen`);
      setFileName(response.data.filename || selectedFile.name);
    } catch (err) {
      console.error(err);
      setUploadMessage("Upload fehlgeschlagen");
    }
  };

  const handleAnalyze = async () => {
    if (!fileName) return;
    setAnalysisStatus("Analyse läuft...");
    try {
      const response = await axios.post(
        "http://localhost:3001/reports/analyze",
        { filename: fileName }
      );
      setAnalysisStatus("");
      setResult(response.data.result || "Vorfälle erkannt");
    } catch (err) {
      console.error(err);
      setAnalysisStatus("");
      setResult("Analyse fehlgeschlagen");
    }
  };

  return (
    
    <div className="max-w-md mx-auto mt-10 p-6 bg-white border border-gray-300 rounded-lg space-y-4">
      <h1 className="text-xl font-semibold mb-2">Berichterstellung</h1>

      {/* Upload */}
      <div className="space-y-2">
        <label className="block text-gray-700">File Auswahl</label>
        <input
          type="file"
          onChange={handleFileChange}
          className="w-full border border-black px-4 py-2 cursor-pointer"
        />
        <button
          onClick={handleUpload}
          className="w-full border border-black px-4 py-2 hover:bg-gray-200 mt-2"
        >
          Hochladen
        </button>
        {uploadMessage && (
          <p className="text-gray-700 text-sm mt-1">{uploadMessage}</p>
        )}
      </div>

      {/* Analyze */}
      {uploadMessage && (
        <div className="space-y-2">
          <button
            onClick={handleAnalyze}
            className="w-full border border-black px-4 py-2 hover:bg-gray-200"
          >
            Analysieren
          </button>
          {analysisStatus && (
            <p className="text-gray-700 text-sm">{analysisStatus}</p>
          )}
          {result && (
            <p className="text-blue-600 text-sm underline cursor-pointer">
              {result}
            </p>
          )}
        </div>
      )}

      {/* Download */}
      {result && (
        <div className="space-y-2">
          <p className="text-gray-700 text-sm">Analyse fertiggestellt</p>
          <DownloadButton fileName={fileName} onError={(msg) => alert(msg)} />
        </div>
      )}
    </div>
  );
}

export default ReportGenerator;
