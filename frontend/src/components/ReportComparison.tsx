/**
 * Component to compare multiple provider reports side-by-side
 */
import React, { useState } from 'react';
import { ProviderReport, ResearchStatus } from '../types';
import { ReportViewer } from './ReportViewer';

interface ReportComparisonProps {
  reports: Record<string, ProviderReport>;
}

export const ReportComparison: React.FC<ReportComparisonProps> = ({ reports }) => {
  const [selectedProvider, setSelectedProvider] = useState<string>('');

  const completedReports = Object.entries(reports).filter(
    ([_, report]) => report.status === ResearchStatus.COMPLETED && report.content
  );

  if (completedReports.length === 0) {
    return (
      <div className="no-reports">
        <p>No completed reports yet. Reports will appear here as they're generated.</p>
      </div>
    );
  }

  // Auto-select first report if none selected
  if (!selectedProvider && completedReports.length > 0) {
    setSelectedProvider(completedReports[0][0]);
  }

  const selectedReport = selectedProvider ? reports[selectedProvider] : null;

  return (
    <div className="report-comparison">
      <div className="provider-tabs">
        {completedReports.map(([providerName, report]) => (
          <button
            key={providerName}
            className={`tab-button ${selectedProvider === providerName ? 'active' : ''}`}
            onClick={() => setSelectedProvider(providerName)}
          >
            {providerName.toUpperCase()}
            <span className="citation-count">
              {report.citations.length} sources
            </span>
          </button>
        ))}
      </div>

      {selectedReport && (
        <ReportViewer
          title={`${selectedProvider.toUpperCase()} Report`}
          content={selectedReport.content}
          citations={selectedReport.citations}
        />
      )}
    </div>
  );
};

