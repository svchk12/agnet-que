import React, { useEffect, useState } from "react";
import { Box, Typography, CircularProgress, Alert } from "@mui/material";

const API_BASE_URL = "http://localhost:8000";

interface JobStatus {
  status: string;
  filename: string;
  summary: string | null;
  checklist: string[] | null;
  started_at: string;
  completed_at: string | null;
  failed_at: string | null;
  error: string | null;
}

interface JobStatusProps {
  jobId: string;
}

export const JobStatus: React.FC<JobStatusProps> = ({ jobId }) => {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
        if (!response.ok) {
          throw new Error("Failed to fetch job status");
        }
        const data = await response.json();
        setStatus(data);
        setError(null);

        // 작업이 완료되거나 실패할 때까지 계속 폴링
        if (data.status !== "completed" && data.status !== "failed") {
          setTimeout(pollStatus, 1000); // 1초마다 폴링
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    };

    pollStatus();
  }, [jobId]);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!status) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6">Job Status: {status.status}</Typography>
      <Typography variant="body2" color="text.secondary">
        File: {status.filename}
      </Typography>

      {status.status === "processing" && (
        <Box sx={{ display: "flex", alignItems: "center", mt: 2 }}>
          <CircularProgress size={20} sx={{ mr: 1 }} />
          <Typography>Processing...</Typography>
        </Box>
      )}

      {status.status === "completed" && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Summary:</Typography>
          <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
            {status.summary}
          </Typography>

          <Typography variant="h6" sx={{ mt: 2 }}>
            Checklist:
          </Typography>
          {status.checklist?.map((item, index) => (
            <Typography key={index} variant="body1">
              • {item}
            </Typography>
          ))}
        </Box>
      )}

      {status.status === "failed" && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {status.error || "An error occurred during processing"}
        </Alert>
      )}
    </Box>
  );
};
