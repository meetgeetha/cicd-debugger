from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from openai import OpenAI
import os
import chromadb
from chromadb.config import Settings

app = FastAPI()

# OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

@app.post("/analyze-log")
async def analyze_log(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")

    # Step 1: Embed log
    embed = client.embeddings.create(
        model="text-embedding-3-small",
        input=content
    )
    vector = embed.data[0].embedding

    # Step 2: Search for similar logs in vector DB
    results = collection.query(
        query_embeddings=[vector],
        n_results=1
    )

    # similar = results.get("documents", [[]])[0]
    # similarity_score = results.get("distances", [[1.0]])[0][0]
    docs = results.get("documents", [[]])
    distances = results.get("distances", [[]])

    has_results = docs and docs[0]

    if has_results:
        similar = docs[0][0]
        similarity_score = distances[0][0]
    else:
        similar = None
        similarity_score = 1.0

    if similar and similarity_score < 0.25:
        stored_fix = results["metadatas"][0][0]
        return JSONResponse({
            "category": stored_fix["category"],
            "severity": stored_fix["severity"],
            "analysis": stored_fix["analysis"],
            "suggested_fix": stored_fix["suggested_fix"],
            "match_type": "Vector match",
            "similarity": similarity_score
        })

    # Step 3: LLM new analysis
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a CI/CD failure expert."},
            {"role": "user", "content": f"Analyze this log:\n\n{content}"}
        ]
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

    # Step 5: Save knowledge
    collection.add(
        documents=[content],
        embeddings=[vector],
        metadatas=[{
            "category": detected,
            "severity": severity,
            "analysis": explanation,
            "suggested_fix": fix
        }],
        ids=[str(hash(content))]
    )

    return JSONResponse({
        "category": detected,
        "severity": severity,
        "analysis": explanation,
        "suggested_fix": fix,
        "match_type": "LLM new analysis",
        "similarity": None
    })
