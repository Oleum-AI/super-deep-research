/**
 * Component to display research progress
 */
import React from 'react';
import { ProviderReport, ResearchStatus } from '../types';

interface ResearchProgressProps {
  reports: Record<string, ProviderReport>;
}

export const ResearchProgress: React.FC<ResearchProgressProps> = ({ reports }) => {
  const getStatusIcon = (status: ResearchStatus) => {
    switch (status) {
      case ResearchStatus.PENDING:
        return '⏳';
      case ResearchStatus.SEARCHING:
        return '🔍';
      case ResearchStatus.ANALYZING:
        return '🧠';
      case ResearchStatus.WRITING:
        return '✍️';
      case ResearchStatus.COMPLETED:
        return '✅';
      case ResearchStatus.FAILED:
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusLabel = (status: ResearchStatus) => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className="research-progress">
      <h3>Research Progress</h3>
      <div className="providers-status">
        {Object.entries(reports).map(([providerName, report]) => (
          <div key={providerName} className={`provider-status ${report.status}`}>
            <div className="provider-header">
              <span className="provider-name">
                {providerName.toUpperCase()}
              </span>
              <span className="status-badge">
                {getStatusIcon(report.status)} {getStatusLabel(report.status)}
              </span>
            </div>
            {report.error && (
              <div className="error-message">Error: {report.error}</div>
            )}
            {report.status === ResearchStatus.COMPLETED && (
              <div className="completion-info">
                ✓ Report completed with {report.citations.length} sources
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

