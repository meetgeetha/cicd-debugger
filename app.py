import requests
import streamlit as st
import pandas as pd
from datetime import datetime
import json

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="AI CI/CD Debugger", page_icon="🛠️", layout="wide")

# Initialize session state
if "history" not in st.session_state:
    st.session_state["history"] = []
if "stats" not in st.session_state:
    st.session_state["stats"] = None

def _display_results(data):
    """Display analysis results"""
    st.success("✅ Analysis Complete!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Category", data.get('category', 'Unknown'))
    with col2:
        sev = data.get("severity", "Medium")
        sev_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(sev, "⚪")
        st.metric("Severity", f"{sev_color} {sev}")
    
    st.divider()
    
    # Match type badge
    match_type = data.get('match_type', 'LLM')
    match_colors = {
        "Exact match": "🟢",
        "Vector match": "🟡",
        "LLM new analysis": "🔵"
    }
    st.caption(f"{match_colors.get(match_type, '⚪')} Match Type: {match_type} | Similarity: {data.get('similarity', 'N/A')}")
    
    if data.get('timestamp'):
        st.caption(f"📅 Analyzed: {data.get('timestamp')}")
    
    # Similar failures if available
    if data.get('similar_failures'):
        with st.expander(f"🔗 View {len(data['similar_failures'])} Similar Failures"):
            for i, similar in enumerate(data['similar_failures'], 1):
                st.write(f"**{i}. {similar.get('category', 'Unknown')}** (Similarity: {similar.get('similarity', 0):.3f})")
                st.caption(f"Timestamp: {similar.get('timestamp', 'Unknown')}")
    
    st.subheader("📋 Analysis")
    st.info(data.get("analysis", "No analysis available."))
    
    st.subheader("🔧 Suggested Fix")
    st.success(data.get("suggested_fix", "No fix suggested."))
    
    # Copy to clipboard button
    fix_text = data.get("suggested_fix", "")
    if fix_text:
        st.code(fix_text, language='text')
    
    # Add to history
    st.session_state["history"].append({
        "Category": data.get("category", "Unknown"),
        "Severity": data.get("severity", "Medium"),
        "Match Type": data.get("match_type", "LLM"),
        "Similarity": f"{data.get('similarity', 'N/A')}",
        "Timestamp": data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    })

# Sidebar for navigation and stats
with st.sidebar:
    st.header("📊 Dashboard")
    
    # Health check
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=5).json()
        if health.get("status") == "healthy":
            st.success("✅ Backend Connected")
            st.caption(f"Total Failures: {health.get('total_failures', 0)}")
        else:
            st.warning("⚠️ Backend Issues")
    except:
        st.error("❌ Backend Unavailable")
    
    st.divider()
    
    # Load statistics
    if st.button("🔄 Refresh Stats"):
        try:
            stats_resp = requests.get(f"{BACKEND_URL}/stats", timeout=5)
            if stats_resp.status_code == 200:
                st.session_state["stats"] = stats_resp.json()
        except:
            st.error("Failed to load stats")
    
    if st.session_state["stats"]:
        stats = st.session_state["stats"]
        st.subheader("📈 Statistics")
        st.metric("Total Failures", stats.get("total_failures", 0))
        
        if stats.get("categories"):
            st.write("**Top Categories:**")
            for cat, count in list(stats.get("top_categories", {}).items())[:5]:
                st.caption(f"{cat}: {count}")
    
    st.divider()
    
    # Export history
    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export History (CSV)",
            data=csv,
            file_name=f"cicd_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    st.divider()
    st.caption("💡 Tip: You can paste log content directly or upload a file")

# Main content
st.title("🛠️ AI CI/CD Debugger")
st.write("Upload CI/CD logs or paste content to get automated failure diagnosis and fix suggestions.")

# Tabs for different input methods
tab1, tab2, tab3 = st.tabs(["📄 Upload File", "📝 Paste Text", "🔍 Search Failures"])

with tab1:
    uploaded_file = st.file_uploader("Upload CI Log File", type=["txt", "log"], help="Upload a log file to analyze")
    
    if uploaded_file is not None:
        st.info("Click **Analyze Log** to process the file.")
        
        if st.button("🔍 Analyze Log", type="primary", use_container_width=True):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            with st.spinner("Analyzing log file... This may take a moment."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/analyze-log", files=files, timeout=120)
                    if resp.status_code == 200:
                        data = resp.json()
                        _display_results(data)
                    else:
                        st.error(f"Backend returned HTTP {resp.status_code}: {resp.text}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The log might be too large or the backend is slow.")
                except Exception as e:
                    st.error(f"Failed to reach backend: {e}")

with tab2:
    st.write("Paste your CI/CD log content directly:")
    text_input = st.text_area("Log Content", height=300, placeholder="Paste your log content here...")
    
    if st.button("🔍 Analyze Text", type="primary", use_container_width=True):
        if not text_input or not text_input.strip():
            st.warning("Please enter some log content to analyze.")
        else:
            with st.spinner("Analyzing log content... This may take a moment."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/analyze-text",
                        json={"content": text_input},
                        timeout=120
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        _display_results(data)
                    else:
                        st.error(f"Backend returned HTTP {resp.status_code}: {resp.text}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The content might be too large.")
                except Exception as e:
                    st.error(f"Failed to reach backend: {e}")

with tab3:
    st.write("Search for similar past failures:")
    search_query = st.text_input("Search Query", placeholder="e.g., 'test failure', 'docker error', 'dependency issue'")
    search_limit = st.slider("Number of results", 1, 20, 5)
    
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not search_query or not search_query.strip():
            st.warning("Please enter a search query.")
        else:
            with st.spinner("Searching for similar failures..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/search",
                        json={"query": search_query, "limit": search_limit},
                        timeout=30
                    )
                    if resp.status_code == 200:
                        results = resp.json()
                        if results.get("results"):
                            st.success(f"Found {results.get('count', 0)} similar failures")
                            for i, result in enumerate(results["results"], 1):
                                with st.expander(f"Result {i}: {result.get('category', 'Unknown')} (Similarity: {result.get('similarity', 0):.3f})"):
                                    st.write(f"**Severity:** {result.get('severity', 'Unknown')}")
                                    st.write(f"**Timestamp:** {result.get('timestamp', 'Unknown')}")
                                    st.write("**Preview:**")
                                    st.code(result.get('preview', ''), language='text')
                        else:
                            st.info("No similar failures found.")
                    else:
                        st.error(f"Search failed: {resp.text}")
                except Exception as e:
                    st.error(f"Search error: {e}")

# History section
if st.session_state["history"]:
    st.divider()
    st.subheader("📊 Analysis History")
    df = pd.DataFrame(st.session_state["history"])
    
    # Add filters
    col1, col2 = st.columns(2)
    with col1:
        categories = ["All"] + list(df["Category"].unique())
        selected_category = st.selectbox("Filter by Category", categories)
    with col2:
        severities = ["All"] + list(df["Severity"].unique())
        selected_severity = st.selectbox("Filter by Severity", severities)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]
    if selected_severity != "All":
        filtered_df = filtered_df[filtered_df["Severity"] == selected_severity]
    
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    if len(filtered_df) < len(df):
        st.caption(f"Showing {len(filtered_df)} of {len(df)} results")
