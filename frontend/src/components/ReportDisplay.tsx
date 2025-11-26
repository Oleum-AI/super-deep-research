import React, { useState } from 'react';
import { ResearchJob, synthesizeReports, MasterReport } from '../api';

interface ReportDisplayProps {
  job: ResearchJob | null;
  onNewMasterReport: (report: MasterReport) => void;
}

const ReportDisplay: React.FC<ReportDisplayProps> = ({ job, onNewMasterReport }) => {
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!job) return null;

  const handleSynthesize = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const masterReport = await synthesizeReports(job.id, selectedProvider);
      onNewMasterReport(masterReport);
    } catch (err) {
      setError('Failed to synthesize reports');
      console.error(err);
    }
    setIsLoading(false);
  };

  return (
    <div>
      <h2>Individual Reports</h2>
      <div style={{ display: 'flex', gap: '1rem', overflowX: 'auto' }}>
        {job.individual_reports.map((report) => (
          <div key={report.id} style={{ flex: '1 0 30%', border: '1px solid #ccc', padding: '1rem' }}>
            <h3>{report.provider}</h3>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{report.report_text}</pre>
          </div>
        ))}
      </div>

      <hr />

      <h2>Synthesize Reports</h2>
      <div>
        <select value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)}>
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="groq">Groq</option>
        </select>
        <button onClick={handleSynthesize} disabled={isLoading}>
          {isLoading ? 'Synthesizing...' : 'Synthesize'}
        </button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>

      {job.master_report && (
        <div>
          <h2>Master Report</h2>
          <div style={{ border: '1px solid #ccc', padding: '1rem' }}>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{job.master_report.report_text}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportDisplay;
