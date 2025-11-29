# 🛠️ AI CI/CD Debugger

An intelligent CI/CD failure analysis tool that uses AI to diagnose build failures, suggest fixes, and learn from past incidents. The system combines vector similarity search with LLM-powered analysis to provide accurate failure diagnosis and remediation suggestions.

## ✨ Features

- **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini to analyze CI/CD failure logs
- **Vector Similarity Search**: Leverages ChromaDB to find similar past failures and reuse known solutions
- **Rule-Based Categorization**: Automatically categorizes failures (Test Failure, Dependency Issue, Build Script Error, Docker Failure, Credential/Permissions)
- **Severity Assessment**: Assigns severity levels (High/Medium) based on failure type
- **Knowledge Base**: Stores analyzed failures in a vector database for future reference
- **Multiple Input Methods**: Upload files or paste log content directly
- **Search Functionality**: Search past failures by text query
- **Statistics Dashboard**: View analytics about stored failures
- **Export History**: Download analysis history as CSV
- **Modern UI**: Beautiful gradient-based interface with card layouts, animations, and professional styling
- **Robust Error Handling**: Comprehensive error messages and validation with encoding support
- **RESTful API**: FastAPI backend with health checks and statistics endpoints

## 🏗️ Architecture

The application consists of two main components:

1. **Backend (FastAPI)**: 
   - `/analyze-log` - Process log files
   - `/analyze-text` - Process log content from text input
   - `/search` - Search for similar past failures
   - `/health` - Health check endpoint
   - `/stats` - Statistics about stored failures
   - Vector database (ChromaDB) for similarity search
   - OpenAI integration for embeddings and LLM analysis
   - Rule-based failure categorization
   - Comprehensive error handling and logging
   - Timestamp tracking for all analyses

2. **Frontend (Streamlit)**:
   - Modern gradient-based UI with card layouts
   - File upload interface with drag-and-drop support
   - Text input for direct log pasting
   - Search interface for past failures
   - Statistics dashboard with real-time metrics
   - Beautiful results display with color-coded severity indicators
   - Analysis history with filtering and CSV export
   - Real-time backend health monitoring
   - Responsive design with smooth animations

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional, for containerized deployment)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/meetgeetha/cicd-debugger.git
   cd cicd-debugger
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variable**
   ```bash
   export OPENAI_API_KEY=your-api-key-here  # Linux/Mac
   # or
   set OPENAI_API_KEY=your-api-key-here  # Windows PowerShell
   ```

5. **Start the backend**
   ```bash
   uvicorn backend:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Start the frontend** (in a new terminal)
   ```bash
   streamlit run app.py --server.port=8501
   ```

7. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t cicd-debugger:latest .
   ```

2. **Run the container**
   ```bash
   docker run --rm -e OPENAI_API_KEY=<your-openai-api-key> -p 8501:8501 -p 8000:8000 cicd-debugger:latest
   ```

3. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000

## 📖 Usage

### Web Interface

1. Open the Streamlit app at http://localhost:8501
2. Choose your input method:
   - **Upload File**: Click "Upload File" tab and select a log file (`.txt` or `.log`)
   - **Paste Text**: Click "Paste Text" tab and paste your log content directly
   - **Search**: Click "Search Failures" tab to find similar past failures
3. Click "Analyze Log" or "Analyze Text" to process
4. View the beautiful results display:
   - **Category**: Type of failure detected with gradient cards
   - **Severity**: Color-coded severity (High=Red, Medium=Yellow, Low=Blue)
   - **Analysis**: Detailed explanation from the AI in styled containers
   - **Suggested Fix**: Actionable remediation steps with code blocks
   - **Match Type**: Visual badges showing match type (Exact/Vector/LLM)
   - **Similar Failures**: View related past failures if available
5. Check the sidebar for:
   - Backend health status
   - Statistics dashboard
   - Export history to CSV

### API Usage

#### Analyze Log File
**Endpoint**: `POST /analyze-log`

**Request**:
```bash
curl -X POST "http://localhost:8000/analyze-log" \
  -F "file=@path/to/your/logfile.log"
```

#### Analyze Text Content
**Endpoint**: `POST /analyze-text`

**Request**:
```bash
curl -X POST "http://localhost:8000/analyze-text" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your log content here..."}'
```

#### Search Past Failures
**Endpoint**: `POST /search`

**Request**:
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test failure", "limit": 5}'
```

#### Health Check
**Endpoint**: `GET /health`

**Request**:
```bash
curl "http://localhost:8000/health"
```

#### Statistics
**Endpoint**: `GET /stats`

**Request**:
```bash
curl "http://localhost:8000/stats"
```

#### Test Upload (Debug)
**Endpoint**: `POST /test-upload`

**Request**:
```bash
curl -X POST "http://localhost:8000/test-upload" \
  -F "file=@path/to/your/logfile.log"
```

Use this endpoint to debug file upload issues.

**Response Example**:
```json
{
  "category": "Test Failure",
  "severity": "High",
  "analysis": "The build failed due to failing unit tests...",
  "suggested_fix": "Run tests locally: `mvn test` or `npm test` and fix failing assertions.",
  "match_type": "Vector match",
  "similarity": 0.15,
  "timestamp": "2024-01-15T10:30:00",
  "similar_failures": [...]
}
```

## 🔍 How It Works

1. **Input**: User uploads a log file or pastes log content
2. **Duplicate Check**: System checks if the exact log was analyzed before (using SHA-256 hash)
3. **Embedding Generation**: The log is converted to a vector embedding using OpenAI's `text-embedding-3-small` model
4. **Similarity Search**: The system searches ChromaDB for similar past failures (cosine similarity < 0.25)
5. **Match Found**: If a similar failure exists, returns the stored analysis and fix with similarity scores
6. **New Analysis**: If no match is found:
   - GPT-4o-mini analyzes the log with structured prompts
   - Rule-based engine categorizes the failure
   - Severity is assigned based on category
   - Timestamp is recorded
   - The failure and solution are stored in the vector database for future reference

## 🆕 New Features & Improvements

### Backend Enhancements
- ✅ **Health Check Endpoint**: Monitor backend status and database connectivity
- ✅ **Statistics API**: Get insights about stored failures (categories, severities, counts)
- ✅ **Text Input Endpoint**: Analyze logs without file upload
- ✅ **Search Endpoint**: Find similar past failures by text query
- ✅ **Robust Error Handling**: Comprehensive error messages with specific details
- ✅ **File Encoding Support**: Automatic UTF-8 and Latin-1 encoding detection with fallback
- ✅ **Logging**: Detailed logging for debugging and monitoring
- ✅ **Timestamp Tracking**: All analyses include timestamps
- ✅ **Improved Duplicate Detection**: SHA-256 hashing for exact matches
- ✅ **CORS Support**: Enable cross-origin requests
- ✅ **Input Validation**: File size limits (100KB), content validation, and empty file checks
- ✅ **Test Endpoint**: `/test-upload` for debugging file upload issues

### Frontend Enhancements
- ✅ **Modern UI Design**: Beautiful gradient-based interface with purple/blue color scheme
- ✅ **Card-Based Layouts**: Professional card designs with shadows and animations
- ✅ **Multiple Input Methods**: Upload files or paste text directly with styled tabs
- ✅ **Search Interface**: Search past failures with similarity scores and color-coded results
- ✅ **Statistics Dashboard**: View metrics in a styled sidebar with glassmorphism effects
- ✅ **Health Monitoring**: Real-time backend status indicator with visual feedback
- ✅ **Enhanced History**: Filterable history with export to CSV
- ✅ **Improved Error Handling**: Specific error messages for different failure scenarios
- ✅ **Loading States**: Beautiful spinners and progress indicators
- ✅ **Similar Failures Display**: View related past failures in expandable cards
- ✅ **Wide Layout**: Better use of screen space with responsive design
- ✅ **Export Functionality**: Download analysis history as CSV
- ✅ **Color-Coded Severity**: Visual indicators (High=Red, Medium=Yellow, Low=Blue)
- ✅ **Match Type Badges**: Visual badges showing analysis type (Exact/Vector/LLM)

## 🗂️ Failure Categories

The system automatically detects these failure types:

- **Test Failure**: Unit test failures, assertion errors
- **Dependency Issue**: Missing packages, version conflicts, npm/maven issues
- **Build Script Error**: Missing scripts, command not found errors
- **Docker Failure**: Dockerfile errors, image build failures
- **Credential/Permissions**: Authentication failures, access denied errors

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required. Your OpenAI API key for embeddings and LLM analysis.

### Database

The vector database (ChromaDB) is stored in the `./db` directory. This directory is automatically created and persists analyzed failures for future similarity searches.

### File Support

- **Supported Formats**: `.txt`, `.log` files
- **Encoding**: UTF-8 (preferred) or Latin-1 (with automatic fallback)
- **Size Limit**: Maximum 100KB per file
- **Content**: Plain text log files only

## 📁 Project Structure

```
cicd-debugger/
├── app.py              # Streamlit frontend
├── backend.py          # FastAPI backend with analysis logic
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── README.md          # This file
└── samples/           # Sample log files for testing
```

## 🧪 Testing

Sample log files are included in the `samples/` directory. You can upload these to test the system:

- `jenkins_build_fail_1.log` - Maven dependency resolution failure
- `jenkins_build_fail_2.log`
- `jenkins_build_fail_3.log`
- `jenkins_build_fail_4.log`
- `jenkins_build_fail_5.log`

### Troubleshooting

If you encounter errors:

1. **400 Bad Request**: 
   - Check that the file is not empty
   - Ensure file is UTF-8 or Latin-1 encoded
   - Verify file size is under 100KB
   - Use `/test-upload` endpoint to debug

2. **503 Service Unavailable**:
   - Verify `OPENAI_API_KEY` is set correctly
   - Check backend logs for details

3. **Connection Errors**:
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify CORS is enabled if accessing from different origin

## 🚢 AWS ECS Deployment

This project is designed for deployment on AWS ECS with Fargate:

- Secure AWS Secrets Manager integration for API keys
- Containerized deployment with both services in one container
- Exposes ports 8000 (FastAPI) and 8501 (Streamlit)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or issues, please open an issue on GitHub.
