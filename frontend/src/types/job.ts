export interface Job {
  jobId: string;
  status: string;
  filename: string;
  summary: string;
  checklist: string[];
  startedAt: string;
  completedAt?: string;
  failedAt?: string;
  error?: string;
}
