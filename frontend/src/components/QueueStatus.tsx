import React from "react";
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from "@mui/material";

interface QueueItem {
  jobId: string;
  filename: string;
  status: "pending" | "processing" | "completed" | "failed";
  position: number;
}

interface QueueStatusProps {
  queue: QueueItem[];
}

const getStatusColor = (status: string) => {
  switch (status) {
    case "pending":
      return { bgcolor: "#fff3e0", color: "#e65100" };
    case "processing":
      return { bgcolor: "#e3f2fd", color: "#1565c0" };
    case "completed":
      return { bgcolor: "#e8f5e9", color: "#2e7d32" };
    case "failed":
      return { bgcolor: "#ffebee", color: "#c62828" };
    default:
      return { bgcolor: "grey.100", color: "grey.700" };
  }
};

export const QueueStatus: React.FC<QueueStatusProps> = ({ queue }) => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        대기열 상태
      </Typography>
      <List>
        {queue.map((job) => (
          <ListItem
            key={job.jobId}
            sx={{
              mb: 1,
              borderRadius: 1,
              backgroundColor: getStatusColor(job.status).bgcolor,
              "&:hover": {
                backgroundColor: getStatusColor(job.status).bgcolor,
                opacity: 0.9,
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
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
