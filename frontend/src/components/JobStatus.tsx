import React, { useEffect, useState } from 'react';
import { getResearchJob, ResearchJob, JobStatus } from '../api';

interface JobStatusProps {
  jobId: number | null;
  onJobCompletion: (job: ResearchJob) => void;
}

const JobStatusDisplay: React.FC<JobStatusProps> = ({ jobId, onJobCompletion }) => {
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const pollJobStatus = async () => {
      try {
        const currentJob = await getResearchJob(jobId);
        setJob(currentJob);
        if (currentJob.status === JobStatus.COMPLETED) {
          onJobCompletion(currentJob);
        } else {
          setTimeout(pollJobStatus, 2000); // Poll every 2 seconds
        }
      } catch (err) {
        setError('Failed to get job status');
        console.error(err);
      }
    };

    pollJobStatus();
  }, [jobId, onJobCompletion]);

  if (!jobId) return null;

  return (
    <div>
      <h2>Job Status</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {job ? (
        <div>
          <p>Job ID: {job.id}</p>
          <p>Status: {job.status}</p>
        </div>
      ) : (
        <p>Loading job status...</p>
      )}
    </div>
  );
};

export default JobStatusDisplay;
