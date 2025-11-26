import { useState } from 'react';
import ResearchForm from './components/ResearchForm';
import ProgressTracker from './components/ProgressTracker';
import ReportViewer from './components/ReportViewer';
import MasterReportView from './components/MasterReport';
import { ResearchSession } from './types';
import { BookOpenIcon } from '@heroicons/react/24/outline';

function App() {
  const [activeSession, setActiveSession] = useState<ResearchSession | null>(null);
  const [showMasterReport, setShowMasterReport] = useState(false);

  const handleResearchStart = (session: ResearchSession) => {
    setActiveSession(session);
    setShowMasterReport(false);
  };

  const handleGenerateMasterReport = () => {
    setShowMasterReport(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BookOpenIcon className="h-8 w-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">Deep Research</h1>
            </div>
            <p className="text-sm text-gray-500">AI-Powered Research Assistant</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!activeSession ? (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Start Your Research
              </h2>
              <p className="text-lg text-gray-600">
                Enter a topic and let multiple AI providers conduct comprehensive research for you.
              </p>
            </div>
            <ResearchForm onResearchStart={handleResearchStart} />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Session Info */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Research Topic: {activeSession.topic}
              </h2>
              <p className="text-sm text-gray-500">
                Session ID: {activeSession.id}
              </p>
            </div>

            {/* Progress Tracker */}
            <ProgressTracker 
              sessionId={activeSession.id}
              onComplete={handleGenerateMasterReport}
            />

            {/* Report Viewer */}
            {showMasterReport ? (
              <MasterReportView sessionId={activeSession.id} />
            ) : (
              <ReportViewer sessionId={activeSession.id} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
