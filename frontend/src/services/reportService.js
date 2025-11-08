import axios from "axios";
const baseUrl = "http://localhost:3001/reports";

export function upload(file) {
  const formData = new FormData();
  formData.append("file", file);
  return axios.post(`${baseUrl}/upload`, formData);
}

export function analyze(filename) {
  return axios.post(`${baseUrl}/analyze`, { filename });
}

export function download(filename) {
  return axios.get(`${baseUrl}/download?filename=${filename}`, { responseType: "blob" });
}