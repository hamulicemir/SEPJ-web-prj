import React from "react";

export default function FileUpload({ onFileSelect }) {
  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <input
      type="file"
      onChange={handleChange}
      className="border border-black p-2 rounded"
    />
  );
}
