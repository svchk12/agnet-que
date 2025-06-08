import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export const fetchJobs = async () => {
  const response = await axios.get(`${API_BASE_URL}/jobs`);
  return response.data;
};

export const fetchJobDetails = async (jobId: string) => {
  const response = await axios.get(`${API_BASE_URL}/jobs/${jobId}`);
  return response.data;
};

export const uploadFile = async (jobId: string, file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(
    `${API_BASE_URL}/jobs/${jobId}/file`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
};
