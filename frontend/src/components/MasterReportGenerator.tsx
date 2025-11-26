/**
 * Component to generate and display master report
 */
import React, { useState } from 'react';
import { ProviderType } from '../types';
import { ReportViewer } from './ReportViewer';

interface MasterReportGeneratorProps {
  sessionId: string;
  masterReport?: string;
  onGenerate: (provider: ProviderType) => void;
  generating: boolean;
}

export const MasterReportGenerator: React.FC<MasterReportGeneratorProps> = ({
  sessionId,
  masterReport,
  onGenerate,
  generating,
}) => {
  const [selectedProvider, setSelectedProvider] = useState<ProviderType>(
    ProviderType.ANTHROPIC
  );

  const providers = [
    { value: ProviderType.OPENAI, label: 'OpenAI (GPT-4)' },
    { value: ProviderType.ANTHROPIC, label: 'Anthropic (Claude)' },
    { value: ProviderType.XAI, label: 'xAI (Grok)' },
  ];

  const handleGenerate = () => {
    onGenerate(selectedProvider);
  };

  return (
    <div className="master-report-generator">
      {!masterReport ? (
        <div className="generation-controls">
          <h3>Generate Master Report</h3>
          <p>
            Synthesize the best insights from all provider reports into a single,
            comprehensive master report.
          </p>

          <div className="provider-selection">
            <label htmlFor="synthesis-provider">
              Choose provider for synthesis:
            </label>
            <select
              id="synthesis-provider"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value as ProviderType)}
              disabled={generating}
            >
              {providers.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="generate-button"
          >
            {generating ? 'Generating...' : 'Generate Master Report'}
          </button>
        </div>
      ) : (
        <ReportViewer
          title="Master Report"
          content={masterReport}
        />
      )}
    </div>
  );
};

