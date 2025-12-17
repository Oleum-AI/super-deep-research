import { useState } from "react";
import { useQuery } from "react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Tab } from "@headlessui/react";
import { Provider, ModelsResponse } from "../types";
import { researchApi } from "../services/api";
import {
  DocumentTextIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

interface ReportViewerProps {
  sessionId: string;
}

const ReportViewer: React.FC<ReportViewerProps> = ({ sessionId }) => {
  const [expandedReports, setExpandedReports] = useState<Set<number>>(
    new Set()
  );
  const [expandedThinking, setExpandedThinking] = useState<Set<number>>(
    new Set()
  );

  // Fetch models from backend
  const { data: modelsData } = useQuery<ModelsResponse>(
    "models",
    researchApi.getModels,
    { staleTime: 5 * 60 * 1000 }
  );

  const {
    data: reports,
    isLoading,
    error,
  } = useQuery(
    ["providerReports", sessionId],
    () => researchApi.getProviderReports(sessionId),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  // Get provider info from backend data
  const getProviderInfo = (provider: Provider) => {
    if (modelsData && modelsData[provider]) {
      const providerData = modelsData[provider];
      const defaultModel =
        providerData.models.find((m) => m.is_default) || providerData.models[0];
      const baseColor = providerData.provider.color
        .replace("bg-", "")
        .replace("-500", "");
      return {
        name: `${providerData.provider.name} - ${
          defaultModel?.display_name || "Unknown"
        }`,
        color: `border-${baseColor}-500 bg-${baseColor}-50`,
        textColor: `text-${baseColor}-700`,
        bgColor: providerData.provider.color,
        thinkingBg: `bg-${baseColor}-100`,
        thinkingBorder: `border-${baseColor}-300`,
      };
    }
    // Fallback
    return {
      name: provider,
      color: "border-gray-500 bg-gray-50",
      textColor: "text-gray-700",
      bgColor: "bg-gray-500",
      thinkingBg: "bg-gray-100",
      thinkingBorder: "border-gray-300",
    };
  };

  const toggleExpanded = (reportId: number) => {
    setExpandedReports((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(reportId)) {
        newSet.delete(reportId);
      } else {
        newSet.add(reportId);
      }
      return newSet;
    });
  };

  const toggleThinking = (reportId: number) => {
    setExpandedThinking((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(reportId)) {
        newSet.delete(reportId);
      } else {
        newSet.add(reportId);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-red-600">Error loading reports</p>
      </div>
    );
  }

  const completedReports = reports?.filter((r) => r.content) || [];
  const pendingReports = reports?.filter((r) => !r.content) || [];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center space-x-2 mb-6">
        <DocumentTextIcon className="h-6 w-6 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-900">
          Individual Provider Reports
        </h3>
      </div>

      {completedReports.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <DocumentTextIcon className="h-12 w-12 mx-auto mb-3 text-gray-400" />
          <p>
            No reports completed yet. Reports will appear here as providers
            finish their research.
          </p>
        </div>
      ) : (
        <Tab.Group>
          <Tab.List className="flex space-x-1 rounded-xl bg-gray-100 p-1">
            {completedReports.map((report) => {
              const info = getProviderInfo(report.provider);
              return (
                <Tab
                  key={report.id}
                  className={({ selected }) =>
                    clsx(
                      "w-full rounded-lg py-2.5 text-sm font-medium leading-5",
                      "ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2",
                      selected
                        ? `${info.bgColor} text-white shadow`
                        : `text-gray-700 hover:bg-white/[0.12] hover:text-gray-900`
                    )
                  }
                >
                  {info.name}
                </Tab>
              );
            })}
          </Tab.List>
          <Tab.Panels className="mt-6">
            {completedReports.map((report) => {
              const info = getProviderInfo(report.provider);
              const isExpanded = expandedReports.has(report.id);
              const isThinkingExpanded = expandedThinking.has(report.id);
              const contentPreview = report.content?.substring(0, 500) || "";
              const hasMore = (report.content?.length || 0) > 500;

              return (
                <Tab.Panel
                  key={report.id}
                  className={clsx("rounded-xl p-6 border-2", info.color)}
                >
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4
                        className={clsx("text-lg font-medium", info.textColor)}
                      >
                        {info.name} Report
                      </h4>
                      {hasMore && (
                        <button
                          onClick={() => toggleExpanded(report.id)}
                          className={clsx(
                            "flex items-center space-x-1 text-sm",
                            info.textColor,
                            "hover:underline"
                          )}
                        >
                          <span>{isExpanded ? "Show Less" : "Show More"}</span>
                          {isExpanded ? (
                            <ChevronUpIcon className="h-4 w-4" />
                          ) : (
                            <ChevronDownIcon className="h-4 w-4" />
                          )}
                        </button>
                      )}
                    </div>

                    {/* Thinking/Reasoning Section - Shown Separately */}
                    {report.thinking && (
                      <div
                        className={clsx(
                          "rounded-lg border overflow-hidden",
                          info.thinkingBorder
                        )}
                      >
                        <button
                          onClick={() => toggleThinking(report.id)}
                          className={clsx(
                            "w-full flex items-center justify-between p-3",
                            info.thinkingBg,
                            "hover:opacity-80 transition-opacity"
                          )}
                        >
                          <div className="flex items-center space-x-2">
                            <LightBulbIcon
                              className={clsx("h-4 w-4", info.textColor)}
                            />
                            <span
                              className={clsx(
                                "text-sm font-medium",
                                info.textColor
                              )}
                            >
                              AI Reasoning Process
                            </span>
                          </div>
                          {isThinkingExpanded ? (
                            <ChevronUpIcon
                              className={clsx("h-4 w-4", info.textColor)}
                            />
                          ) : (
                            <ChevronDownIcon
                              className={clsx("h-4 w-4", info.textColor)}
                            />
                          )}
                        </button>

                        {isThinkingExpanded && (
                          <div className="p-3 bg-white/50 border-t border-gray-200">
                            <div className="prose prose-sm max-w-none text-gray-700">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {report.thinking}
                              </ReactMarkdown>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Report Content */}
                    <div
                      className={clsx(
                        "markdown-content prose prose-sm max-w-none bg-white/50 p-4 rounded-lg",
                        !isExpanded &&
                          hasMore &&
                          "max-h-96 overflow-hidden relative"
                      )}
                    >
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {isExpanded || !hasMore
                          ? report.content || ""
                          : contentPreview + "..."}
                      </ReactMarkdown>

                      {!isExpanded && hasMore && (
                        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent" />
                      )}
                    </div>

                    <div className="text-xs text-gray-500 pt-4 border-t border-gray-200">
                      Generated at:{" "}
                      {new Date(report.createdAt).toLocaleString()}
                    </div>
                  </div>
                </Tab.Panel>
              );
            })}
          </Tab.Panels>
        </Tab.Group>
      )}

      {pendingReports.length > 0 && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            Waiting for reports from:{" "}
            {pendingReports
              .map((r) => getProviderInfo(r.provider).name)
              .join(", ")}
          </p>
        </div>
      )}
    </div>
  );
};

export default ReportViewer;
