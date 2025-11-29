from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import os
import chromadb
from chromadb.config import Settings
import logging
from datetime import datetime
import hashlib
from typing import Optional, List
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CI/CD Debugger API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY not set. Some features may not work.")
client = OpenAI(api_key=api_key) if api_key else None

# # Initialize Vector DB
# chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="./db"))
# collection = chroma_client.get_or_create_collection("cicd_failures")

settings = Settings(
    allow_reset=True,
    anonymized_telemetry=False,
    chroma_db_impl="duckdb+parquet",
    persist_directory="./db"
)

chroma_client = chromadb.PersistentClient(path="./db")
collection = chroma_client.get_or_create_collection(
    "cicd_failures",
    metadata={"hnsw:space": "cosine"}
)


# Failure Categories & Fixes (Rule Engine)
failure_categories = {
    "Test Failure": ["test", "assert", "failure", "surefire"],
    "Dependency Issue": ["dependency", "resolve", "artifact", "package", "npm", "requirements.txt"],
    "Build Script Error": ["missing script", "no such file", "command not found"],
    "Docker Failure": ["docker", "image", "container", "dockerfile"],
    "Credential/Permissions": ["permission", "credential", "unauthorized", "access denied"],
}

suggested_fixes = {
    "Test Failure": "Run tests locally: `mvn test` or `npm test` and fix failing assertions.",
    "Dependency Issue": "Check version numbers, run `npm install` or `mvn -U clean install`.",
    "Build Script Error": "Add or correct build script in package.json.",
    "Docker Failure": "Fix Dockerfile or verify packages exist. Test using `docker build .`",
    "Credential/Permissions": "Ensure Jenkins secrets / AWS IAM permissions are configured.",
}

# Pydantic models
class LogAnalysisRequest(BaseModel):
    content: str

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        count = collection.count()
        return JSONResponse({
            "status": "healthy",
            "database": "connected",
            "total_failures": count,
            "openai_configured": client is not None
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)

@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Test endpoint to debug file uploads"""
    try:
        file_content = await file.read()
        return JSONResponse({
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "preview": file_content[:100].decode("utf-8", errors="ignore") if file_content else "Empty"
        })
    except Exception as e:
        logger.error(f"Test upload error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/stats")
async def get_statistics():
    """Get statistics about stored failures"""
    try:
        count = collection.count()
        if count == 0:
            return JSONResponse({
                "total_failures": 0,
                "categories": {},
                "severities": {},
                "by_match_type": {}
            })
        
        # Get all metadata
        all_data = collection.get()
        metadatas = all_data.get("metadatas", [])
        
        categories = Counter([m.get("category", "Unknown") for m in metadatas])
        severities = Counter([m.get("severity", "Medium") for m in metadatas])
        
        return JSONResponse({
            "total_failures": count,
            "categories": dict(categories),
            "severities": dict(severities),
            "top_categories": dict(categories.most_common(5))
        })
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-text")
async def analyze_text(request: LogAnalysisRequest):
    """Analyze log content from text input"""
    try:
        if not request.content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        content = request.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Content cannot be empty (only whitespace)")
        
        if len(content) > 100000:  # Limit to 100KB
            raise HTTPException(status_code=400, detail=f"Content too large ({len(content)} bytes, max 100KB)")
        
        logger.info(f"Processing text input, size: {len(content)} bytes")
        return await _analyze_log_content(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.post("/analyze-log")
async def analyze_log(file: UploadFile = File(...)):
    """Analyze log from file upload"""
    try:
        # Check if file was provided (FastAPI will raise if File(...) is missing, but double-check)
        if file is None:
            raise HTTPException(status_code=400, detail="No file provided in request")
        
        # Read file content
        file_content = await file.read()
        
        if not file_content or len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty or could not be read (0 bytes)")
        
        # Try to decode with UTF-8, fallback to other encodings
        try:
            content = file_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file_content.decode("latin-1")
                logger.warning(f"File decoded with latin-1 instead of utf-8: {file.filename or 'unnamed'}")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400, 
                    detail="File encoding not supported. Please use UTF-8 or Latin-1 encoded text files."
                )
        
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="File is empty (no text content after decoding)")
        
        if len(content) > 100000:  # Limit to 100KB
            raise HTTPException(
                status_code=400, 
                detail=f"File too large ({len(content)} bytes, max 100KB). Please use a smaller file."
            )
        
        filename = file.filename or "unnamed_file"
        logger.info(f"Processing file: {filename}, size: {len(content)} bytes, content_type: {file.content_type}")
        return await _analyze_log_content(content)
    except HTTPException:
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error: {e}")
        raise HTTPException(status_code=400, detail=f"File encoding error: {str(e)}")
    except Exception as e:
        logger.error(f"Error reading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def _analyze_log_content(content: str):
    """Core analysis logic"""
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")
    
    try:
        # Generate unique ID using hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Check if this exact log was already analyzed
        existing = collection.get(ids=[content_hash])
        if existing and existing.get("ids"):
            stored_meta = existing["metadatas"][0]
            return JSONResponse({
                "category": stored_meta["category"],
                "severity": stored_meta["severity"],
                "analysis": stored_meta["analysis"],
                "suggested_fix": stored_meta["suggested_fix"],
                "match_type": "Exact match",
                "similarity": 0.0,
                "timestamp": stored_meta.get("timestamp", "Unknown")
            })
        
        # Step 1: Embed log
        logger.info("Generating embeddings...")
        embed = client.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        vector = embed.data[0].embedding

        # Step 2: Search for similar logs in vector DB
        logger.info("Searching for similar failures...")
        results = collection.query(
            query_embeddings=[vector],
            n_results=3  # Get top 3 similar
        )

        docs = results.get("documents", [[]])
        distances = results.get("distances", [[]])
        metadatas = results.get("metadatas", [[]])

        has_results = docs and docs[0]

        if has_results and distances[0][0] < 0.25:
            similar_meta = metadatas[0][0]
            return JSONResponse({
                "category": similar_meta["category"],
                "severity": similar_meta["severity"],
                "analysis": similar_meta["analysis"],
                "suggested_fix": similar_meta["suggested_fix"],
                "match_type": "Vector match",
                "similarity": float(distances[0][0]),
                "similar_failures": [
                    {
                        "category": m.get("category"),
                        "similarity": float(d),
                        "timestamp": m.get("timestamp", "Unknown")
                    }
                    for m, d in zip(metadatas[0][:3], distances[0][:3])
                ]
            })

        # Step 3: LLM new analysis
        logger.info("Performing LLM analysis...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a CI/CD failure expert. Provide concise, actionable analysis."},
                {"role": "user", "content": f"Analyze this CI/CD failure log and provide:\n1. Root cause\n2. Impact\n3. Step-by-step fix\n\nLog:\n\n{content[:5000]}"}  # Limit to 5000 chars for LLM
            ],
            temperature=0.3
        )
        explanation = response.choices[0].message.content

        # Step 4: Rule-based category detection
        detected = "Unknown"
        for category, keywords in failure_categories.items():
            if any(word.lower() in content.lower() for word in keywords):
                detected = category
                break

        severity = "High" if detected in ["Test Failure", "Dependency Issue"] else "Medium"
        fix = suggested_fixes.get(detected, "Investigate further manually.")

        # Step 5: Save knowledge with timestamp
        timestamp = datetime.now().isoformat()
        collection.add(
            documents=[content],
            embeddings=[vector],
            metadatas=[{
                "category": detected,
                "severity": severity,
                "analysis": explanation,
                "suggested_fix": fix,
                "timestamp": timestamp
            }],
            ids=[content_hash]
        )
        
        logger.info(f"Saved new failure: {detected} ({severity})")

        return JSONResponse({
            "category": detected,
            "severity": severity,
            "analysis": explanation,
            "suggested_fix": fix,
            "match_type": "LLM new analysis",
            "similarity": None,
            "timestamp": timestamp
        })
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/search")
async def search_failures(request: SearchRequest):
    """Search for similar failures by text query"""
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")
    
    try:
        # Embed the search query
        embed = client.embeddings.create(
            model="text-embedding-3-small",
            input=request.query
        )
        vector = embed.data[0].embedding
        
        # Search
        results = collection.query(
            query_embeddings=[vector],
            n_results=request.limit or 5
        )
        
        docs = results.get("documents", [[]])
        distances = results.get("distances", [[]])
        metadatas = results.get("metadatas", [[]])
        ids = results.get("ids", [[]])
        
        if not docs or not docs[0]:
            return JSONResponse({"results": [], "count": 0})
        
        results_list = []
        for i, (doc, dist, meta, id_val) in enumerate(zip(docs[0], distances[0], metadatas[0], ids[0])):
            results_list.append({
                "id": id_val,
                "category": meta.get("category"),
                "severity": meta.get("severity"),
                "similarity": float(dist),
                "timestamp": meta.get("timestamp", "Unknown"),
                "preview": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        return JSONResponse({
            "results": results_list,
            "count": len(results_list),
            "query": request.query
        })
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
