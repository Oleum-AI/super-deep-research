import { useState } from 'react';
import { useMutation } from 'react-query';
import toast from 'react-hot-toast';
import { ResearchRequest, ResearchSession, Provider } from '../types';
import { researchApi } from '../services/api';
import { BeakerIcon, SparklesIcon } from '@heroicons/react/24/outline';

interface ResearchFormProps {
  onResearchStart: (session: ResearchSession) => void;
}

const ResearchForm: React.FC<ResearchFormProps> = ({ onResearchStart }) => {
  const [topic, setTopic] = useState('');
  const [selectedProviders, setSelectedProviders] = useState<Provider[]>([
    Provider.OPENAI,
    Provider.ANTHROPIC,
    Provider.XAI,
  ]);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [includeWebSearch, setIncludeWebSearch] = useState(true);

  const startResearchMutation = useMutation(
    (request: ResearchRequest) => researchApi.startResearch(request),
    {
      onSuccess: (session) => {
        toast.success('Research started successfully!');
        onResearchStart(session);
      },
      onError: (error: any) => {
        toast.error(error?.response?.data?.detail || 'Failed to start research');
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!topic.trim()) {
      toast.error('Please enter a research topic');
      return;
    }

    if (selectedProviders.length === 0) {
      toast.error('Please select at least one provider');
      return;
    }

    startResearchMutation.mutate({
      topic: topic.trim(),
      providers: selectedProviders,
      maxTokens,
      includeWebSearch,
    });
  };

  const toggleProvider = (provider: Provider) => {
    setSelectedProviders((prev) =>
      prev.includes(provider)
        ? prev.filter((p) => p !== provider)
        : [...prev, provider]
    );
  };

  const providerInfo = {
    [Provider.OPENAI]: {
      name: 'OpenAI Deep Research',
      description: 'Autonomous web research with real-time data',
      color: 'bg-green-500',
    },
    [Provider.ANTHROPIC]: {
      name: 'Claude Sonnet 4.5',
      description: 'Extended thinking for deep insights',
      color: 'bg-purple-500',
    },
    [Provider.XAI]: {
      name: 'xAI Grok 2',
      description: 'Technical depth and innovation focus',
      color: 'bg-blue-500',
    },
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Topic Input */}
      <div>
        <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
          Research Topic
        </label>
        <textarea
          id="topic"
          rows={3}
          className="input w-full px-4 py-2 border rounded-lg"
          placeholder="Enter your research topic or question..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={startResearchMutation.isLoading}
        />
      </div>

      {/* Provider Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select AI Providers
        </label>
        <div className="space-y-3">
          {Object.values(Provider).map((provider) => {
            const info = providerInfo[provider];
            return (
              <label
                key={provider}
                className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={selectedProviders.includes(provider)}
                  onChange={() => toggleProvider(provider)}
                  disabled={startResearchMutation.isLoading}
                />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full ${info.color}`}></span>
                    <span className="font-medium">{info.name}</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{info.description}</p>
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Advanced Options */}
      <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-700">Advanced Options</h3>
        
        <div>
          <label htmlFor="maxTokens" className="block text-sm font-medium text-gray-700 mb-1">
            Max Tokens: {maxTokens}
          </label>
          <input
            type="range"
            id="maxTokens"
            min="1000"
            max="16000"
            step="1000"
            value={maxTokens}
            onChange={(e) => setMaxTokens(Number(e.target.value))}
            className="w-full"
            disabled={startResearchMutation.isLoading}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1,000</span>
            <span>16,000</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="webSearch"
            checked={includeWebSearch}
            onChange={(e) => setIncludeWebSearch(e.target.checked)}
            disabled={startResearchMutation.isLoading}
          />
          <label htmlFor="webSearch" className="text-sm text-gray-700">
            Include web search capabilities (simulated)
          </label>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={startResearchMutation.isLoading}
        className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors ${
          startResearchMutation.isLoading
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-primary-600 text-white hover:bg-primary-700'
        }`}
      >
        {startResearchMutation.isLoading ? (
          <>
            <BeakerIcon className="h-5 w-5 animate-pulse" />
            <span>Starting Research...</span>
          </>
        ) : (
          <>
            <SparklesIcon className="h-5 w-5" />
            <span>Start Research</span>
          </>
        )}
      </button>
    </form>
  );
};

export default ResearchForm;
