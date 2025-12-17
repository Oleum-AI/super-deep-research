import { useState, useEffect } from "react";
import { useMutation, useQuery } from "react-query";
import toast from "react-hot-toast";
import {
  ResearchRequest,
  ResearchSession,
  Provider,
  ModelsResponse,
  ProviderSettings,
  ModelConfig,
} from "../types";
import { researchApi } from "../services/api";
import {
  BeakerIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from "@heroicons/react/24/outline";

interface ResearchFormProps {
  onResearchStart: (session: ResearchSession) => void;
}

interface ProviderSelection {
  enabled: boolean;
  selectedModel: string;
  maxTokens: number;
}

const ResearchForm: React.FC<ResearchFormProps> = ({ onResearchStart }) => {
  const [topic, setTopic] = useState("");
  const [providerSelections, setProviderSelections] = useState<
    Record<string, ProviderSelection>
  >({});
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(
    new Set()
  );
  const [showTokenSettings, setShowTokenSettings] = useState(false);

  // Fetch available models from backend
  const { data: modelsData, isLoading: modelsLoading } =
    useQuery<ModelsResponse>("models", researchApi.getModels, {
      staleTime: 5 * 60 * 1000, // Cache for 5 minutes
      onError: () => {
        toast.error("Failed to load available models");
      },
    });

  // Initialize provider selections when models data loads
  useEffect(() => {
    if (modelsData) {
      const initialSelections: Record<string, ProviderSelection> = {};
      Object.values(Provider).forEach((provider) => {
        const providerData = modelsData[provider];
        if (providerData) {
          const defaultModel =
            providerData.models.find((m) => m.is_default) ||
            providerData.models[0];
          const defaultTokens = Math.min(
            Math.floor(defaultModel.max_output_tokens / 2),
            4096
          );
          initialSelections[provider] = {
            enabled: true, // All providers enabled by default
            selectedModel: defaultModel.name,
            maxTokens: defaultTokens,
          };
        }
      });
      setProviderSelections(initialSelections);
    }
  }, [modelsData]);

  const startResearchMutation = useMutation(
    (request: ResearchRequest) => researchApi.startResearch(request),
    {
      onSuccess: (session) => {
        toast.success("Research started successfully!");
        onResearchStart(session);
      },
      onError: (error: any) => {
        toast.error(
          error?.response?.data?.detail || "Failed to start research"
        );
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!topic.trim()) {
      toast.error("Please enter a research topic");
      return;
    }

    const selectedProviders = Object.entries(providerSelections)
      .filter(([_, sel]) => sel.enabled)
      .map(([provider]) => provider as Provider);

    if (selectedProviders.length === 0) {
      toast.error("Please select at least one provider");
      return;
    }

    // Build provider settings with selected models and max tokens
    const settings: Record<string, ProviderSettings> = {};
    selectedProviders.forEach((provider) => {
      const sel = providerSelections[provider];
      settings[provider] = {
        model: sel.selectedModel,
        maxTokens: sel.maxTokens,
      };
    });

    startResearchMutation.mutate({
      topic: topic.trim(),
      providers: selectedProviders,
      providerSettings: settings,
    });
  };

  const toggleProvider = (provider: Provider) => {
    setProviderSelections((prev) => ({
      ...prev,
      [provider]: { ...prev[provider], enabled: !prev[provider]?.enabled },
    }));
  };

  const selectModel = (provider: Provider, modelName: string) => {
    const providerData = modelsData?.[provider];
    const model = providerData?.models.find((m) => m.name === modelName);
    const defaultTokens = model
      ? Math.min(Math.floor(model.max_output_tokens / 2), 4096)
      : 4096;

    setProviderSelections((prev) => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        selectedModel: modelName,
        maxTokens: defaultTokens, // Reset to reasonable default when model changes
      },
    }));
  };

  const updateMaxTokens = (provider: Provider, maxTokens: number) => {
    setProviderSelections((prev) => ({
      ...prev,
      [provider]: { ...prev[provider], maxTokens },
    }));
  };

  const toggleProviderExpanded = (provider: string) => {
    setExpandedProviders((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(provider)) {
        newSet.delete(provider);
      } else {
        newSet.add(provider);
      }
      return newSet;
    });
  };

  const getSelectedModel = (provider: Provider): ModelConfig | undefined => {
    const providerData = modelsData?.[provider];
    const selection = providerSelections[provider];
    return providerData?.models.find(
      (m) => m.name === selection?.selectedModel
    );
  };

  const formatNumber = (num: number) => num.toLocaleString();

  if (modelsLoading) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
        Loading available models...
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Topic Input */}
      <div>
        <label
          htmlFor="topic"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
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

      {/* Provider & Model Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select AI Providers & Models
        </label>
        <div className="space-y-3">
          {Object.values(Provider).map((provider) => {
            const providerData = modelsData?.[provider];
            const selection = providerSelections[provider];
            const isEnabled = selection?.enabled ?? false;
            const isExpanded = expandedProviders.has(provider);
            const selectedModel = getSelectedModel(provider);

            if (!providerData) return null;

            return (
              <div
                key={provider}
                className={`border rounded-lg transition-colors ${
                  isEnabled
                    ? "border-primary-300 bg-primary-50"
                    : "border-gray-200 bg-white"
                }`}
              >
                {/* Provider Header */}
                <div className="flex items-center p-4">
                  <input
                    type="checkbox"
                    className="mr-3"
                    checked={isEnabled}
                    onChange={() => toggleProvider(provider)}
                    disabled={startResearchMutation.isLoading}
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`w-2 h-2 rounded-full ${providerData.provider.color}`}
                      ></span>
                      <span className="font-medium">
                        {providerData.provider.name}
                      </span>
                    </div>
                    {selectedModel && (
                      <p className="text-sm text-gray-600 mt-1">
                        Selected:{" "}
                        <span className="font-medium">
                          {selectedModel.display_name}
                        </span>
                      </p>
                    )}
                  </div>
                  {isEnabled && providerData.models.length > 1 && (
                    <button
                      type="button"
                      onClick={() => toggleProviderExpanded(provider)}
                      className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronUpIcon className="h-5 w-5" />
                      ) : (
                        <ChevronDownIcon className="h-5 w-5" />
                      )}
                    </button>
                  )}
                </div>

                {/* Model Selection (expanded) */}
                {isEnabled &&
                  (isExpanded || providerData.models.length === 1) && (
                    <div className="border-t border-gray-200 p-4 bg-white/50">
                      <p className="text-xs text-gray-500 mb-3">
                        Select a model:
                      </p>
                      <div className="space-y-2">
                        {providerData.models.map((model) => (
                          <label
                            key={model.name}
                            className={`flex items-start p-3 rounded-lg border cursor-pointer transition-all ${
                              selection?.selectedModel === model.name
                                ? "border-primary-400 bg-primary-100"
                                : "border-gray-200 hover:border-gray-300 bg-white"
                            }`}
                          >
                            <input
                              type="radio"
                              name={`model-${provider}`}
                              className="mt-1 mr-3"
                              checked={selection?.selectedModel === model.name}
                              onChange={() => selectModel(provider, model.name)}
                              disabled={startResearchMutation.isLoading}
                            />
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-gray-900">
                                  {model.display_name}
                                  {model.is_default && (
                                    <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                                      default
                                    </span>
                                  )}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mt-1">
                                {model.description}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">
                                Max output:{" "}
                                {formatNumber(model.max_output_tokens)} tokens
                              </p>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Advanced Token Settings Toggle */}
      <button
        type="button"
        onClick={() => setShowTokenSettings(!showTokenSettings)}
        className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
      >
        <AdjustmentsHorizontalIcon className="h-4 w-4" />
        <span>{showTokenSettings ? "Hide" : "Show"} Token Settings</span>
      </button>

      {/* Per-Provider Token Settings */}
      {showTokenSettings && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-700">Max Output Tokens</h3>
          <p className="text-xs text-gray-500 mb-4">
            Adjust the maximum response length for each selected provider.
          </p>

          {Object.values(Provider).map((provider) => {
            const selection = providerSelections[provider];
            if (!selection?.enabled) return null;

            const selectedModel = getSelectedModel(provider);
            if (!selectedModel) return null;

            const providerData = modelsData?.[provider];
            const maxTokens = selectedModel.max_output_tokens;
            const minTokens = 1000;

            return (
              <div key={provider} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`w-2 h-2 rounded-full ${providerData?.provider.color}`}
                    ></span>
                    <span className="text-sm font-medium text-gray-700">
                      {providerData?.provider.name} -{" "}
                      {selectedModel.display_name}
                    </span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {formatNumber(selection.maxTokens)} tokens
                  </span>
                </div>
                <input
                  type="range"
                  min={minTokens}
                  max={maxTokens}
                  step={1000}
                  value={selection.maxTokens}
                  onChange={(e) =>
                    updateMaxTokens(provider, Number(e.target.value))
                  }
                  className="w-full"
                  disabled={startResearchMutation.isLoading}
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{formatNumber(minTokens)}</span>
                  <span>{formatNumber(maxTokens)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={startResearchMutation.isLoading}
        className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors ${
          startResearchMutation.isLoading
            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
            : "bg-primary-600 text-white hover:bg-primary-700"
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
