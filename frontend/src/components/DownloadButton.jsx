import React from "react";
import axios from "axios";

export default function DownloadButton({ fileName, onError }) {
  const handleDownload = async () => {
    try {
      const response = await axios.get(
        `http://localhost:3001/reports/download?filename=${fileName}`,
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName || "bericht.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error("Download fehlgeschlagen", err);
      onError("Fehler beim Download");
    }
  };

  return (
    <button
      onClick={handleDownload}
      className="border border-black px-6 py-2 mt-4 hover:bg-gray-200"
    >
      Bericht downloaden
    </button>
  );
}
