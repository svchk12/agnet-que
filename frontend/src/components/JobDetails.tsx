import React from "react";
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  Divider,
} from "@mui/material";
import { Job } from "../types/job";

interface JobDetailsProps {
  job: Job;
}

const JobDetails: React.FC<JobDetailsProps> = ({ job }) => {
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch (error) {
      return "알 수 없음";
    }
  };

  const decodeUnicode = (text: string) => {
    try {
      return text.replace(/\\u([0-9a-fA-F]{4})/g, (_, code) =>
        String.fromCharCode(parseInt(code, 16))
      );
    } catch (error) {
      return text;
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 3,
        mb: 3,
        maxHeight: "80vh",
        overflow: "auto",
      }}
    >
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          작업 상세
        </Typography>
        <Box
          sx={{
            display: "flex",
            gap: 3,
            color: "text.secondary",
            fontSize: "0.875rem",
          }}
        >
          <Typography variant="body2">작업 ID: {job.jobId}</Typography>
          <Typography variant="body2">
            시작 시간: {formatDate(job.startedAt)}
          </Typography>
          {job.completedAt && (
            <Typography variant="body2">
              완료 시간: {formatDate(job.completedAt)}
            </Typography>
          )}
        </Box>
      </Box>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxHeight: "300px",
            overflow: "auto",
            backgroundColor: "background.default",
          }}
        >
          <Typography variant="h6" gutterBottom>
            요약
          </Typography>
          <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
            {decodeUnicode(job.summary)}
          </Typography>
        </Paper>

        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxHeight: "300px",
            overflow: "auto",
            backgroundColor: "background.default",
          }}
        >
          <Typography variant="h6" gutterBottom>
            체크리스트
          </Typography>
          <List>
            {job.checklist.map((item, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={false}
                    tabIndex={-1}
                    disableRipple
                  />
                </ListItemIcon>
                <ListItemText primary={decodeUnicode(item)} />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Box>
    </Paper>
  );
};

export default JobDetails;
