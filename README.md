# Deep Research Application

A powerful multi-provider AI research application that conducts extensive deep research using multiple frontier LLM providers (OpenAI, Anthropic, xAI) simultaneously, then intelligently merges the results into a comprehensive master report.

## Features

- 🔍 **Multi-Provider Research**: Conduct research using OpenAI GPT-4, Anthropic Claude, and xAI Grok in parallel
- 🎯 **Intelligent Report Merging**: Automatically merge insights from all providers into a cohesive master report
- 📊 **Real-time Progress Tracking**: Monitor research progress with WebSocket-powered live updates
- 📄 **PDF Export**: Export your research reports to beautifully formatted PDFs
- 🎨 **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- 💾 **Persistent Storage**: SQLite database for storing research sessions and reports

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **UV** - Fast Python package manager
- **LLM SDKs** - OpenAI, Anthropic, and custom xAI integration
- **ReportLab** - PDF generation
- **WebSockets** - Real-time communication

### Frontend
- **React** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and caching
- **React Markdown** - Markdown rendering

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- UV (Python package manager)
- API keys for OpenAI, Anthropic, and xAI

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd super-deep-research
   ```

2. **Set up the backend**
   ```bash
   cd backend
   
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your API keys
   # OPENAI_API_KEY=your_key_here
   # ANTHROPIC_API_KEY=your_key_here
   # XAI_API_KEY=your_key_here
   
   # Install dependencies with UV
   uv sync
   ```

3. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

The easiest way to run both backend and frontend is using the provided start script:

```bash
# From the root directory
chmod +x start.sh
./start.sh
```

This will:
- Start the FastAPI backend on http://localhost:8001
- Start the React frontend on http://localhost:5173
- Handle proper shutdown with Ctrl+C

Alternatively, you can run them separately:

**Backend:**
```bash
cd backend
uv run python main.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Usage

1. **Start a Research Session**
   - Enter your research topic in the form
   - Select which AI providers to use
   - Configure advanced options (max tokens, web search)
   - Click "Start Research"

2. **Monitor Progress**
   - Watch real-time progress updates for each provider
   - View individual reports as they complete
   - Reports are displayed in a tabbed interface

3. **Generate Master Report**
   - Once all providers complete, click "Generate Master Report"
   - Choose which provider to use for merging
   - The system will intelligently combine all reports

4. **Export to PDF**
   - Click "Export to PDF" to download your research
   - PDFs are professionally formatted with proper styling

## Architecture

### Backend Structure
```
backend/
├── main.py              # FastAPI application
├── models.py            # Database models and Pydantic schemas
├── config.py            # Configuration management
└── services/
    ├── llm_providers.py # LLM provider implementations
    ├── research_orchestrator.py # Parallel research execution
    ├── report_merger.py # Intelligent report merging
    └── pdf_export.py    # PDF generation
```

### Frontend Structure
```
frontend/
├── src/
│   ├── App.tsx          # Main application component
│   ├── components/      # React components
│   │   ├── ResearchForm.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── ReportViewer.tsx
│   │   └── MasterReport.tsx
│   ├── services/        # API and WebSocket services
│   └── types/           # TypeScript type definitions
```

## API Endpoints

- `POST /api/research/start` - Start a new research session
- `GET /api/research/{session_id}/status` - Get research progress
- `GET /api/research/{session_id}/reports` - Get individual provider reports
- `POST /api/research/{session_id}/merge` - Generate master report
- `GET /api/research/{session_id}/export/pdf` - Export to PDF
- `WebSocket /ws/research/{session_id}` - Real-time updates

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:
- API keys for each LLM provider
- Server ports
- Database URL
- CORS settings

### Adding New Providers

To add a new LLM provider:
1. Create a new provider class in `services/` extending `BaseProvider`
2. Add the provider to the `Provider` enum in `models.py`
3. Register it in `LLMProviderService`
4. Update the frontend types and UI

## Development

### Backend Development
```bash
cd backend
uv run python main.py  # Hot reload enabled
```

### Frontend Development
```bash
cd frontend
npm run dev  # Vite dev server with HMR
```

### Type Checking
```bash
cd frontend
npm run build  # TypeScript compilation
```

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
