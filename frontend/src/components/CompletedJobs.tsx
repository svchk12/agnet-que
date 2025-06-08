import React from "react";
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Chip,
} from "@mui/material";

interface CompletedJob {
  jobId: string;
  filename: string;
  completedAt: string;
  hasSummary: boolean;
  status: string;
}

interface CompletedJobsProps {
  jobs: CompletedJob[];
  selectedJobId: string | null;
  onSelectJob: (jobId: string) => void;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case "completed":
      return { bgcolor: "#e8f5e9", color: "#2e7d32" };
    case "failed":
      return { bgcolor: "#ffebee", color: "#c62828" };
    default:
      return { bgcolor: "grey.100", color: "grey.700" };
  }
};

export const CompletedJobs: React.FC<CompletedJobsProps> = ({
  jobs,
  selectedJobId,
  onSelectJob,
}) => {
  return (
    <Box sx={{ p: 2, height: "100%", overflow: "auto" }}>
      <Typography variant="h6" gutterBottom>
        완료된 작업
      </Typography>
      <List>
        {jobs.map((job) => (
          <ListItem key={job.jobId} disablePadding>
            <ListItemButton
              selected={selectedJobId === job.jobId}
              onClick={() => onSelectJob(job.jobId)}
              sx={{
                mb: 1,
                borderRadius: 1,
                backgroundColor: getStatusColor(job.status).bgcolor,
                "&:hover": {
                  backgroundColor: getStatusColor(job.status).bgcolor,
                  opacity: 0.9,
                },
                "&.Mui-selected": {
                  backgroundColor: getStatusColor(job.status).bgcolor,
                  opacity: 0.7,
                },
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      ID: {job.jobId}
                    </Typography>
                    <Chip
                      label={job.status}
                      size="small"
                      onClick={(e) => e.stopPropagation()}
                      sx={{
                        backgroundColor: getStatusColor(job.status).color,
                        color: "white",
                        fontWeight: "bold",
                      }}
                    />
                  </Box>
                }
                secondary={job.filename}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
