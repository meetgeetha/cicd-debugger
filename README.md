# 🛠️ AI CI/CD Debugger

An intelligent CI/CD failure analysis tool that uses AI to diagnose build failures, suggest fixes, and learn from past incidents. The system combines vector similarity search with LLM-powered analysis to provide accurate failure diagnosis and remediation suggestions.

## ✨ Features

- **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini to analyze CI/CD failure logs
- **Vector Similarity Search**: Leverages ChromaDB to find similar past failures and reuse known solutions
- **Rule-Based Categorization**: Automatically categorizes failures (Test Failure, Dependency Issue, Build Script Error, Docker Failure, Credential/Permissions)
- **Severity Assessment**: Assigns severity levels (High/Medium) based on failure type
- **Knowledge Base**: Stores analyzed failures in a vector database for future reference
- **Web Interface**: User-friendly Streamlit UI for uploading and analyzing logs
- **RESTful API**: FastAPI backend for programmatic access

## 🏗️ Architecture

The application consists of two main components:

1. **Backend (FastAPI)**: 
   - `/analyze-log` endpoint that processes log files
   - Vector database (ChromaDB) for similarity search
   - OpenAI integration for embeddings and LLM analysis
   - Rule-based failure categorization

2. **Frontend (Streamlit)**:
   - File upload interface
   - Results display with category, severity, analysis, and suggested fixes
   - Analysis history tracking

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
2. Click "Upload CI Log" and select a log file (`.txt` or `.log`)
3. Click "Analyze Log" to process the file
4. View the results:
   - **Category**: Type of failure detected
   - **Severity**: High or Medium
   - **Analysis**: Detailed explanation from the AI
   - **Suggested Fix**: Actionable remediation steps
   - **Match Type**: Whether it matched a previous failure or was newly analyzed

### API Usage

**Endpoint**: `POST /analyze-log`

**Request**:
```bash
curl -X POST "http://localhost:8000/analyze-log" \
  -F "file=@path/to/your/logfile.log"
```

**Response**:
```json
{
  "category": "Test Failure",
  "severity": "High",
  "analysis": "The build failed due to failing unit tests...",
  "suggested_fix": "Run tests locally: `mvn test` or `npm test` and fix failing assertions.",
  "match_type": "Vector match",
  "similarity": 0.15
}
```

## 🔍 How It Works

1. **Log Upload**: User uploads a CI/CD failure log file
2. **Embedding Generation**: The log is converted to a vector embedding using OpenAI's `text-embedding-3-small` model
3. **Similarity Search**: The system searches ChromaDB for similar past failures (cosine similarity < 0.25)
4. **Match Found**: If a similar failure exists, returns the stored analysis and fix
5. **New Analysis**: If no match is found:
   - GPT-4o-mini analyzes the log
   - Rule-based engine categorizes the failure
   - Severity is assigned based on category
   - The failure and solution are stored in the vector database for future reference

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

- `jenkins_build_fail_1.log`
- `jenkins_build_fail_2.log`
- `jenkins_build_fail_3.log`
- `jenkins_build_fail_4.log`
- `jenkins_build_fail_5.log`

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
