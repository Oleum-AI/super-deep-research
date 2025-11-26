import { useState } from 'react';
import { useMutation, useQuery } from 'react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import toast from 'react-hot-toast';
import { MasterReport as MasterReportType, Provider } from '../types';
import { researchApi } from '../services/api';
import { 
  DocumentArrowDownIcon, 
  DocumentMagnifyingGlassIcon,
  SparklesIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface MasterReportProps {
  sessionId: string;
}

const MasterReport: React.FC<MasterReportProps> = ({ sessionId }) => {
  const [selectedMergeProvider, setSelectedMergeProvider] = useState<Provider>(Provider.OPENAI);
  const [masterReport, setMasterReport] = useState<MasterReportType | null>(null);

  // Generate master report mutation
  const generateMutation = useMutation(
    () => researchApi.generateMasterReport(sessionId, selectedMergeProvider),
    {
      onSuccess: (report) => {
        setMasterReport(report);
        toast.success('Master report generated successfully!');
      },
      onError: (error: any) => {
        toast.error(error?.response?.data?.detail || 'Failed to generate master report');
      },
    }
  );

  // Export to PDF mutation
  const exportPDFMutation = useMutation(
    () => researchApi.exportToPDF(sessionId),
    {
      onSuccess: (blob) => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `research_report_${sessionId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        toast.success('PDF exported successfully!');
      },
      onError: (error: any) => {
        toast.error('Failed to export PDF');
      },
    }
  );

  const providerOptions = [
    { value: Provider.OPENAI, name: 'OpenAI Deep Research', description: 'Best for web-researched synthesis' },
    { value: Provider.ANTHROPIC, name: 'Claude Sonnet 4.5', description: 'Best for deep reasoning' },
    { value: Provider.XAI, name: 'xAI Grok 2', description: 'Best for technical accuracy' },
  ];

  const handleGenerateReport = () => {
    generateMutation.mutate();
  };

  const handleExportPDF = () => {
    if (!masterReport) {
      toast.error('Generate master report first');
      return;
    }
    exportPDFMutation.mutate();
  };

  if (!masterReport) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-12">
          <DocumentMagnifyingGlassIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Generate Master Report</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Combine insights from all providers into a single, comprehensive report
          </p>

          {/* Provider Selection */}
          <div className="max-w-md mx-auto mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2 text-left">
              Select provider for merging:
            </label>
            <div className="space-y-2">
              {providerOptions.map((option) => (
                <label
                  key={option.value}
                  className={clsx(
                    'flex items-start p-3 rounded-lg border-2 cursor-pointer transition-all',
                    selectedMergeProvider === option.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                >
                  <input
                    type="radio"
                    className="mt-1"
                    checked={selectedMergeProvider === option.value}
                    onChange={() => setSelectedMergeProvider(option.value)}
                    disabled={generateMutation.isLoading}
                  />
                  <div className="ml-3 flex-1 text-left">
                    <div className="font-medium text-gray-900">{option.name}</div>
                    <div className="text-sm text-gray-600">{option.description}</div>
                  </div>
                  {selectedMergeProvider === option.value && (
                    <CheckIcon className="h-5 w-5 text-primary-600 ml-2 mt-1" />
                  )}
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={generateMutation.isLoading}
            className={clsx(
              'inline-flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-colors',
              generateMutation.isLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            )}
          >
            {generateMutation.isLoading ? (
              <>
                <SparklesIcon className="h-5 w-5 animate-pulse" />
                <span>Generating Master Report...</span>
              </>
            ) : (
              <>
                <SparklesIcon className="h-5 w-5" />
                <span>Generate Master Report</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Master Report Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-semibold text-gray-900">Master Research Report</h3>
            <p className="text-sm text-gray-600 mt-1">
              Synthesized by {providerOptions.find(p => p.value === selectedMergeProvider)?.name}
            </p>
          </div>
          <button
            onClick={handleExportPDF}
            disabled={exportPDFMutation.isLoading}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors"
          >
            {exportPDFMutation.isLoading ? (
              <>
                <DocumentArrowDownIcon className="h-5 w-5 animate-pulse" />
                <span>Exporting...</span>
              </>
            ) : (
              <>
                <DocumentArrowDownIcon className="h-5 w-5" />
                <span>Export to PDF</span>
              </>
            )}
          </button>
        </div>
        
        <div className="text-sm text-gray-500">
          Generated at: {new Date(masterReport.createdAt).toLocaleString()}
        </div>
      </div>

      {/* Master Report Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="markdown-content prose prose-lg max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {masterReport.content}
          </ReactMarkdown>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Want to regenerate with a different provider?
          </p>
          <button
            onClick={() => {
              setMasterReport(null);
              setSelectedMergeProvider(Provider.OPENAI);
            }}
            className="text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            Generate New Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default MasterReport;
