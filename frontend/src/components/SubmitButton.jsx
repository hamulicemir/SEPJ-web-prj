import React from "react";
import axios from "axios";

export default function SubmitButton({ file, onSuccess, onError }) {
  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:3001/reports/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.status === 200) {
        onSuccess && onSuccess();
      } else {
        onError && onError("Upload fehlgeschlagen");
      }
    } catch (err) {
      console.error("Upload fehlgeschlagen", err);
      onError && onError("Fehler beim Upload");
    }
  };

  return (
    <button
      onClick={handleUpload}
      disabled={!file}
      className="border border-black px-6 py-2 mt-4 hover:bg-gray-200 disabled:opacity-50"
    >
      Bericht generieren
    </button>
  );
}
