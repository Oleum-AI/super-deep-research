# Quick Setup Guide

## Prerequisites

1. **Python 3.11+** - Check with `python3 --version`
2. **Node.js 18+** - Check with `node --version`
3. **UV** - Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Getting Your API Keys

### OpenAI (GPT-4)
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

### Anthropic (Claude)
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)

### xAI (Grok)
1. Go to https://console.x.ai/
2. Navigate to API Keys
3. Create a new API key
4. Copy the key

### Brave Search
1. Go to https://api.search.brave.com/
2. Sign up for an account
3. Subscribe to the API (free tier available)
4. Copy your API key

## Installation Steps

### 1. Set up environment variables

```bash
# Copy the example file
cp backend/env.example backend/.env

# Edit the file with your favorite editor
nano backend/.env  # or vim, code, etc.
```

Add your API keys:
```env
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
XAI_API_KEY=your-xai-key-here
BRAVE_SEARCH_API_KEY=your-brave-search-key-here
```

### 2. Run the application

```bash
./start.sh
```

The script will automatically:
- Install all Python dependencies
- Install all Node.js dependencies
- Start the backend server
- Start the frontend development server

### 3. Access the application

Open your browser and navigate to:
- **Frontend**: http://localhost:5173
- **API Health Check**: http://localhost:8001/api/health

## First Research Session

1. Enter a research topic (e.g., "What are the latest developments in quantum computing?")
2. Select one or more providers (OpenAI, Anthropic, xAI)
3. Adjust the number of sources if needed
4. Click "Start Research"
5. Watch the progress as each provider conducts research
6. View individual reports as they complete
7. (Optional) Generate a master report combining all insights

## Troubleshooting

### "Command not found: uv"
Install UV with:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Port 8001 already in use"
The script will automatically kill the process. If it persists:
```bash
lsof -ti:8001 | xargs kill -9
```

### "API key invalid"
Double-check your API keys in `backend/.env`. Make sure:
- No spaces around the `=` sign
- No quotes around the keys
- Keys are copied completely

### Research fails immediately
Check the browser console (F12) for errors. Common issues:
- Invalid API key
- Brave Search API quota exceeded
- Network connectivity issues

## Development Mode

### Backend only
```bash
cd backend
uv sync
uv run python main.py
```

### Frontend only
```bash
cd frontend
npm install
npm run dev
```

## Stopping the Application

Press `Ctrl+C` in the terminal where `start.sh` is running. The script will automatically stop both services.

## Need Help?

- Check the main README.md for detailed documentation
- Open an issue on GitHub
- Review the API documentation at http://localhost:8001/docs (when running)

