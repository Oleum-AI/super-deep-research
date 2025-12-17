import { useEffect, useState } from "react";
import { useQuery } from "react-query";
import {
  ResearchProgress,
  ResearchStatus,
  Provider,
  WebSocketMessage,
  ModelsResponse,
} from "../types";
import { researchApi } from "../services/api";
import { webSocketService } from "../services/websocket";
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/solid";
import clsx from "clsx";

interface ProgressTrackerProps {
  sessionId: string;
  onComplete: () => void;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  sessionId,
  onComplete,
}) => {
  const [webSocketUpdates, setWebSocketUpdates] = useState<Record<string, any>>(
    {}
  );

  // Fetch models from backend
  const { data: modelsData } = useQuery<ModelsResponse>(
    "models",
    researchApi.getModels,
    { staleTime: 5 * 60 * 1000 }
  );

  // Query for initial status
  const { data: progress } = useQuery(
    ["researchProgress", sessionId],
    () => researchApi.getResearchStatus(sessionId),
    {
      refetchInterval: 5000, // Poll every 5 seconds as fallback
    }
  );

  // WebSocket connection for real-time updates
  useEffect(() => {
    webSocketService.connect(sessionId);

    const cleanup = webSocketService.onMessage((message: WebSocketMessage) => {
      if (message.type === "research_update" && message.provider) {
        setWebSocketUpdates((prev) => ({
          ...prev,
          [message.provider]: {
            status: message.status,
            progress: message.progress,
            error: message.error,
          },
        }));
      }
    });

    return () => {
      cleanup();
      webSocketService.disconnect();
    };
  }, [sessionId]);

  // Get provider info from backend data
  const getProviderInfo = (provider: Provider) => {
    if (modelsData && modelsData[provider]) {
      const providerData = modelsData[provider];
      const defaultModel =
        providerData.models.find((m) => m.is_default) || providerData.models[0];
      return {
        name: `${providerData.provider.name} - ${
          defaultModel?.display_name || "Unknown"
        }`,
        color: providerData.provider.color,
        lightColor: providerData.provider.color
          .replace("bg-", "bg-")
          .replace("-500", "-100"),
        textColor: providerData.provider.color
          .replace("bg-", "text-")
          .replace("-500", "-700"),
      };
    }
    // Fallback
    return {
      name: provider,
      color: "bg-gray-500",
      lightColor: "bg-gray-100",
      textColor: "text-gray-700",
    };
  };

  const getProviderStatus = (provider: string) => {
    const wsUpdate = webSocketUpdates[provider];
    const apiStatus = progress?.providers[provider];

    return {
      status: wsUpdate?.status || apiStatus?.status || ResearchStatus.PENDING,
      progress: wsUpdate?.progress || 0,
      error: wsUpdate?.error || apiStatus?.error,
      hasContent: apiStatus?.hasContent || false,
    };
  };

  const getStatusIcon = (status: ResearchStatus) => {
    switch (status) {
      case ResearchStatus.COMPLETED:
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case ResearchStatus.FAILED:
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case ResearchStatus.IN_PROGRESS:
        return (
          <ArrowPathIcon className="h-5 w-5 text-primary-500 animate-spin" />
        );
      default:
        return <div className="h-5 w-5 rounded-full bg-gray-300" />;
    }
  };

  const getStatusText = (status: ResearchStatus) => {
    switch (status) {
      case ResearchStatus.COMPLETED:
        return "Complete";
      case ResearchStatus.FAILED:
        return "Failed";
      case ResearchStatus.IN_PROGRESS:
        return "In Progress";
      case ResearchStatus.PENDING:
        return "Waiting";
      default:
        return status;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Research Progress
      </h3>

      <div className="space-y-4">
        {Object.values(Provider).map((provider) => {
          const info = getProviderInfo(provider);
          const status = getProviderStatus(provider);
          const progressPercent = Math.round(status.progress * 100);

          return (
            <div key={provider} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${info.color}`} />
                  <span className="font-medium text-gray-700">{info.name}</span>
                  {getStatusIcon(status.status)}
                </div>
                <span
                  className={clsx(
                    "text-sm font-medium",
                    status.status === ResearchStatus.COMPLETED
                      ? "text-green-600"
                      : status.status === ResearchStatus.FAILED
                      ? "text-red-600"
                      : status.status === ResearchStatus.IN_PROGRESS
                      ? "text-primary-600"
                      : "text-gray-500"
                  )}
                >
                  {getStatusText(status.status)}
                </span>
              </div>

              {/* Progress Bar */}
              {status.status === ResearchStatus.IN_PROGRESS && (
                <div className="relative pt-1">
                  <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
                    <div
                      style={{ width: `${progressPercent}%` }}
                      className={clsx(
                        "shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center transition-all duration-500",
                        info.color
                      )}
                    />
                  </div>
                </div>
              )}

              {/* Error Message */}
              {status.error && (
                <p className="text-sm text-red-600 mt-1">{status.error}</p>
              )}
            </div>
          );
        })}
      </div>

      {/* Overall Status */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">
            Overall Status
          </span>
          <span
            className={clsx(
              "text-sm font-semibold",
              progress?.overallStatus === ResearchStatus.COMPLETED
                ? "text-green-600"
                : progress?.overallStatus === ResearchStatus.FAILED
                ? "text-red-600"
                : progress?.overallStatus === ResearchStatus.IN_PROGRESS
                ? "text-primary-600"
                : "text-gray-500"
            )}
          >
            {progress?.overallStatus
              ? getStatusText(progress.overallStatus)
              : "Loading..."}
          </span>
        </div>

        {progress?.overallStatus === ResearchStatus.COMPLETED && (
          <button
            onClick={onComplete}
            className="mt-4 w-full btn-primary py-2 px-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Generate Master Report
          </button>
        )}
      </div>
    </div>
  );
};

export default ProgressTracker;
