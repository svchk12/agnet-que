import React, { useState, useEffect } from "react";
import { Box, Container, Typography, Paper } from "@mui/material";
import { FileUpload } from "../components/FileUpload";
import { QueueStatus } from "../components/QueueStatus";
import { CompletedJobs } from "../components/CompletedJobs";
import JobDetails from "../components/JobDetails";

const containerStyles = {
  maxWidth: "100%",
  margin: "0 auto",
  padding: "20px",
  height: "100vh",
  display: "flex",
  flexDirection: "column",
  width: "100%",
};

const contentStyles = {
  display: "flex",
  gap: 2,
  flex: 1,
  mt: 2,
  minHeight: 0,
  width: "100%",
};

const panelStyles = {
  flex: 1,
  overflow: "hidden",
  display: "flex",
  flexDirection: "column",
  width: "100%",
};

const queuePanelStyles = {
  ...panelStyles,
  flex: "0 0 250px",
};

const completedPanelStyles = {
  ...panelStyles,
  flex: "0 0 250px",
};

const detailsPanelStyles = {
  ...panelStyles,
  flex: "1 1 auto",
  minWidth: "400px",
};

export const Home: React.FC = () => {
  const [queue, setQueue] = useState<any[]>([]);
  const [completedJobs, setCompletedJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [selectedJobDetails, setSelectedJobDetails] = useState<any>(null);

  const handleFileUpload = (jobId: string, filename: string) => {
    // 새로운 작업을 큐에 추가
    setQueue((prev) => [
      ...prev,
      {
        jobId,
        filename,
        status: "pending",
        position: prev.length + 1,
      },
    ]);
  };

  const handleSelectJob = async (jobId: string) => {
    try {
      console.log("Selected job ID:", jobId);
      setSelectedJobId(jobId);

      const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
      console.log("API Response status:", response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("API Response data:", data);

      // API 응답 형식에 맞게 데이터 변환
      const transformedData = {
        id: jobId,
        status: data.status || "unknown",
        startedAt: data.createdAt || null,
        completedAt: data.updatedAt || null,
        failedAt: null,
        summary: data.result?.summary || "",
        checklist: data.result?.checklist || [],
        error: null,
      };

      console.log("Transformed job details:", transformedData);
      setSelectedJobDetails(transformedData);
    } catch (error) {
      console.error("Error fetching job details:", error);
      setSelectedJobDetails(null);
    }
  };

  // 작업 상태 폴링
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      if (queue.length === 0) return;

      try {
        const updatedJobs = await Promise.all(
          queue.map(async (job) => {
            try {
              console.log("Polling job:", job.jobId);
              const response = await fetch(
                `http://localhost:8000/jobs/${job.jobId}`
              );
              console.log("Poll response status:", response.status);

              if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
              }

              const data = await response.json();
              console.log("Poll response data:", data);

              // API 응답 형식에 맞게 데이터 변환
              const transformedData = {
                jobId: job.jobId,
                status: data.status || "unknown",
                startedAt: data.createdAt || null,
                completedAt: data.updatedAt || null,
                failedAt: null,
                summary: data.result?.summary || "",
                checklist: data.result?.checklist || [],
                error: null,
              };

              console.log("Transformed job data:", transformedData);

              // 완료된 작업 처리
              if (data.status === "completed" || data.status === "failed") {
                setCompletedJobs((prev) => {
                  const exists = prev.some((j) => j.jobId === job.jobId);
                  if (!exists) {
                    return [...prev, transformedData];
                  }
                  return prev;
                });
                return null; // 대기열에서 제거
              }

              return transformedData;
            } catch (error) {
              console.error(
                `Failed to fetch status for job ${job.jobId}:`,
                error
              );
              return job;
            }
          })
        );

        // null이 아닌 작업만 필터링
        const activeJobs = updatedJobs.filter((job) => job !== null);
        console.log("Updated active jobs:", activeJobs);
        setQueue(activeJobs);
      } catch (error) {
        console.error("Error polling job statuses:", error);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [queue]);

  return (
    <Container sx={containerStyles} maxWidth={false}>
      <Typography variant="h4" gutterBottom>
        문서 처리 시스템
      </Typography>
      <Paper sx={{ p: 2 }}>
        <FileUpload onUploadComplete={handleFileUpload} />
      </Paper>
      <Box sx={contentStyles}>
        <Paper sx={queuePanelStyles}>
          <QueueStatus queue={queue} />
        </Paper>
        <Paper sx={completedPanelStyles}>
          <CompletedJobs
            jobs={completedJobs}
            selectedJobId={selectedJobId}
            onSelectJob={handleSelectJob}
          />
        </Paper>
        <Paper sx={detailsPanelStyles}>
          {selectedJobId && (
            <JobDetails
              job={{
                jobId: selectedJobId,
                status: selectedJobDetails?.status || "pending",
                filename: selectedJobDetails?.filename || "",
                summary: selectedJobDetails?.summary || "",
                checklist: selectedJobDetails?.checklist || [],
                startedAt:
                  selectedJobDetails?.startedAt || new Date().toISOString(),
                completedAt: selectedJobDetails?.completedAt,
                failedAt: selectedJobDetails?.failedAt,
                error: selectedJobDetails?.error,
              }}
            />
          )}
        </Paper>
      </Box>
    </Container>
  );
};
