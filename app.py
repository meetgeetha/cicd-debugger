import requests
import streamlit as st
import pandas as pd
from datetime import datetime
import json

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI CI/CD Debugger", 
    page_icon="🛠️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, appealing design
st.markdown("""
    <style>
    /* Main styling */
    .main {
        padding-top: 2rem;
    }
    
    /* Header styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    /* Card styling */
    .stMetric {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.6);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .status-high {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
    }
    
    .status-medium {
        background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
        color: white;
    }
    
    .status-low {
        background: linear-gradient(135deg, #48dbfb 0%, #0abde3 100%);
        color: white;
    }
    
    /* Result cards */
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    /* Info boxes */
    .stInfo {
        background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%);
        border-left: 4px solid #26a69a;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-left: 4px solid #4caf50;
    }
    
    /* Metric containers */
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        background: #f8f9fa;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "history" not in st.session_state:
    st.session_state["history"] = []
if "stats" not in st.session_state:
    st.session_state["stats"] = None

def _display_results(data):
    """Display analysis results with modern, appealing design"""
    # Success banner
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; 
                    border-radius: 12px; 
                    margin-bottom: 2rem;
                    text-align: center;
                    color: white;
                    font-size: 1.2rem;
                    font-weight: 600;'>
            ✅ Analysis Complete!
        </div>
    """, unsafe_allow_html=True)
    
    # Metrics in a nice grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category = data.get('category', 'Unknown')
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; 
                        border-radius: 12px; 
                        text-align: center;
                        color: white;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <div style='font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;'>CATEGORY</div>
                <div style='font-size: 1.5rem; font-weight: 700;'>{category}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sev = data.get("severity", "Medium")
        sev_colors = {
            "High": "linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)",
            "Medium": "linear-gradient(135deg, #feca57 0%, #ff9ff3 100%)",
            "Low": "linear-gradient(135deg, #48dbfb 0%, #0abde3 100%)"
        }
        sev_gradient = sev_colors.get(sev, "linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%)")
        st.markdown(f"""
            <div style='background: {sev_gradient}; 
                        padding: 1.5rem; 
                        border-radius: 12px; 
                        text-align: center;
                        color: white;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <div style='font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;'>SEVERITY</div>
                <div style='font-size: 1.5rem; font-weight: 700;'>{sev}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        match_type = data.get('match_type', 'LLM')
        similarity = data.get('similarity', 'N/A')
        if similarity != 'N/A' and similarity is not None:
            similarity_display = f"{float(similarity):.3f}"
        else:
            similarity_display = "N/A"
        
        match_colors = {
            "Exact match": "linear-gradient(135deg, #00b894 0%, #00cec9 100%)",
            "Vector match": "linear-gradient(135deg, #feca57 0%, #ff9ff3 100%)",
            "LLM new analysis": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        }
        match_gradient = match_colors.get(match_type, "linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%)")
        st.markdown(f"""
            <div style='background: {match_gradient}; 
                        padding: 1.5rem; 
                        border-radius: 12px; 
                        text-align: center;
                        color: white;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <div style='font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;'>MATCH TYPE</div>
                <div style='font-size: 1.1rem; font-weight: 700;'>{match_type}</div>
                <div style='font-size: 0.8rem; opacity: 0.9; margin-top: 0.5rem;'>Similarity: {similarity_display}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Timestamp
    if data.get('timestamp'):
        st.markdown(f"""
            <div style='text-align: center; color: #666; margin-bottom: 1.5rem;'>
                📅 Analyzed: {data.get('timestamp')}
            </div>
        """, unsafe_allow_html=True)
    
    # Similar failures in a nice card
    if data.get('similar_failures'):
        with st.expander(f"🔗 View {len(data['similar_failures'])} Similar Failures", expanded=False):
            for i, similar in enumerate(data['similar_failures'], 1):
                st.markdown(f"""
                    <div style='background: #f8f9fa; 
                                padding: 1rem; 
                                border-radius: 8px; 
                                margin: 0.5rem 0;
                                border-left: 4px solid #667eea;'>
                        <div style='font-weight: 600; color: #333; margin-bottom: 0.5rem;'>
                            {i}. {similar.get('category', 'Unknown')}
                        </div>
                        <div style='font-size: 0.85rem; color: #666;'>
                            Similarity: <strong>{similar.get('similarity', 0):.3f}</strong> | 
                            Timestamp: {similar.get('timestamp', 'Unknown')}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Analysis section with styled container
    st.markdown("""
        <div style='background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%); 
                    padding: 1.5rem; 
                    border-radius: 12px; 
                    border-left: 5px solid #26a69a;
                    margin: 1.5rem 0;'>
            <h3 style='color: #00695c; margin-top: 0;'>📋 Analysis</h3>
        </div>
    """, unsafe_allow_html=True)
    
    analysis_text = data.get("analysis", "No analysis available.")
    st.markdown(f"""
        <div style='background: white; 
                    padding: 1.5rem; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    line-height: 1.6;
                    color: #333;'>
            {analysis_text}
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Suggested fix section
    st.markdown("""
        <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                    padding: 1.5rem; 
                    border-radius: 12px; 
                    border-left: 5px solid #4caf50;
                    margin: 1.5rem 0;'>
            <h3 style='color: #2e7d32; margin-top: 0;'>🔧 Suggested Fix</h3>
        </div>
    """, unsafe_allow_html=True)
    
    fix_text = data.get("suggested_fix", "No fix suggested.")
    st.markdown(f"""
        <div style='background: white; 
                    padding: 1.5rem; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    line-height: 1.6;
                    color: #333;'>
            {fix_text}
        </div>
    """, unsafe_allow_html=True)
    
    # Code block for fix if available
    if fix_text and fix_text != "No fix suggested.":
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
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: white; font-size: 2rem; margin: 0;'>📊 Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Health check with styled card
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=5).json()
        if health.get("status") == "healthy":
            st.markdown(f"""
                <div style='background: rgba(255,255,255,0.2); 
                            padding: 1rem; 
                            border-radius: 10px; 
                            margin: 1rem 0;
                            backdrop-filter: blur(10px);'>
                    <div style='color: white; font-weight: 600; margin-bottom: 0.5rem;'>✅ Backend Connected</div>
                    <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem;'>
                        Total Failures: <strong>{health.get('total_failures', 0)}</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Backend Issues")
    except:
        st.markdown("""
            <div style='background: rgba(255,0,0,0.2); 
                        padding: 1rem; 
                        border-radius: 10px; 
                        margin: 1rem 0;
                        color: white;'>
                ❌ Backend Unavailable
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Load statistics with styled button
    if st.button("🔄 Refresh Stats", use_container_width=True):
        try:
            stats_resp = requests.get(f"{BACKEND_URL}/stats", timeout=5)
            if stats_resp.status_code == 200:
                st.session_state["stats"] = stats_resp.json()
                st.success("Stats updated!")
        except:
            st.error("Failed to load stats")
    
    if st.session_state["stats"]:
        stats = st.session_state["stats"]
        st.markdown("""
            <div style='background: rgba(255,255,255,0.15); 
                        padding: 1.5rem; 
                        border-radius: 10px; 
                        margin: 1rem 0;
                        backdrop-filter: blur(10px);'>
            <h3 style='color: white; margin-top: 0;'>📈 Statistics</h3>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.3); 
                        padding: 1rem; 
                        border-radius: 8px; 
                        text-align: center;
                        margin: 0.5rem 0;
                        color: white;'>
                <div style='font-size: 0.9rem; opacity: 0.9;'>Total Failures</div>
                <div style='font-size: 2rem; font-weight: 700;'>{stats.get('total_failures', 0)}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if stats.get("categories"):
            st.markdown("<div style='color: white; font-weight: 600; margin-top: 1rem;'>Top Categories:</div>", unsafe_allow_html=True)
            for cat, count in list(stats.get("top_categories", {}).items())[:5]:
                st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.2); 
                                padding: 0.5rem 1rem; 
                                border-radius: 6px; 
                                margin: 0.25rem 0;
                                color: white;
                                display: flex;
                                justify-content: space-between;'>
                        <span>{cat}</span>
                        <strong>{count}</strong>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Export history
    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export History (CSV)",
            data=csv,
            file_name=f"cicd_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background: rgba(255,255,255,0.1); 
                    padding: 1rem; 
                    border-radius: 8px; 
                    color: rgba(255,255,255,0.9);
                    font-size: 0.85rem;
                    text-align: center;'>
            💡 Tip: You can paste log content directly or upload a file
        </div>
    """, unsafe_allow_html=True)

# Main content with gradient header
st.markdown("""
    <div style='text-align: center; padding: 2rem 0; margin-bottom: 2rem;'>
        <h1 style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 3.5rem;
                    font-weight: 800;
                    margin-bottom: 1rem;'>
            🛠️ AI CI/CD Debugger
        </h1>
        <p style='font-size: 1.2rem; color: #666; max-width: 600px; margin: 0 auto;'>
            Upload CI/CD logs or paste content to get automated failure diagnosis and fix suggestions
        </p>
    </div>
""", unsafe_allow_html=True)

# Tabs for different input methods
tab1, tab2, tab3 = st.tabs(["📄 Upload File", "📝 Paste Text", "🔍 Search Failures"])

with tab1:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                    padding: 2rem; 
                    border-radius: 12px; 
                    margin-bottom: 2rem;
                    text-align: center;'>
            <h3 style='color: #333; margin-top: 0;'>📤 Upload Your Log File</h3>
            <p style='color: #666;'>Select a log file from your computer to analyze</p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a log file", 
        type=["txt", "log"], 
        help="Upload a log file to analyze",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        st.markdown(f"""
            <div style='background: #e8f5e9; 
                        padding: 1rem; 
                        border-radius: 8px; 
                        border-left: 4px solid #4caf50;
                        margin: 1rem 0;'>
                <strong>📄 {uploaded_file.name}</strong> ready to analyze
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Analyze Log", type="primary", use_container_width=True):
            try:
                # Prepare file for upload
                file_content = uploaded_file.getvalue()
                if not file_content:
                    st.error("❌ File appears to be empty. Please select a valid log file.")
                else:
                    files = {"file": (uploaded_file.name, file_content, uploaded_file.type or "text/plain")}
                    with st.spinner("🔍 Analyzing log file... This may take a moment."):
                        try:
                            resp = requests.post(f"{BACKEND_URL}/analyze-log", files=files, timeout=120)
                            if resp.status_code == 200:
                                data = resp.json()
                                _display_results(data)
                            elif resp.status_code == 400:
                                error_detail = resp.text
                                try:
                                    error_json = resp.json()
                                    error_detail = error_json.get("detail", error_detail)
                                except:
                                    pass
                                st.error(f"❌ Bad Request (400): {error_detail}")
                            elif resp.status_code == 503:
                                st.error("❌ Service Unavailable: OpenAI API key not configured or backend issue.")
                            else:
                                st.error(f"❌ Backend returned HTTP {resp.status_code}: {resp.text}")
                        except requests.exceptions.Timeout:
                            st.error("⏱️ Request timed out. The log might be too large or the backend is slow.")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Cannot connect to backend. Make sure the backend is running on http://localhost:8000")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Failed to process file: {str(e)}")

with tab2:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                    padding: 2rem; 
                    border-radius: 12px; 
                    margin-bottom: 2rem;
                    text-align: center;'>
            <h3 style='color: #333; margin-top: 0;'>📝 Paste Log Content</h3>
            <p style='color: #666;'>Copy and paste your CI/CD log content directly into the text area</p>
        </div>
    """, unsafe_allow_html=True)
    
    text_input = st.text_area(
        "Log Content", 
        height=300, 
        placeholder="Paste your log content here...\n\nExample:\n[ERROR] Build failed\nTest suite failed with 5 errors\n...",
        label_visibility="collapsed"
    )
    
    if st.button("🔍 Analyze Text", type="primary", use_container_width=True):
        if not text_input or not text_input.strip():
            st.warning("⚠️ Please enter some log content to analyze.")
        else:
            with st.spinner("🔍 Analyzing log content... This may take a moment."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/analyze-text",
                        json={"content": text_input},
                        timeout=120,
                        headers={"Content-Type": "application/json"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        _display_results(data)
                    elif resp.status_code == 400:
                        error_detail = resp.text
                        try:
                            error_json = resp.json()
                            error_detail = error_json.get("detail", error_detail)
                        except:
                            pass
                        st.error(f"❌ Bad Request (400): {error_detail}")
                    elif resp.status_code == 503:
                        st.error("❌ Service Unavailable: OpenAI API key not configured or backend issue.")
                    else:
                        st.error(f"❌ Backend returned HTTP {resp.status_code}: {resp.text}")
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. The content might be too large.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure the backend is running on http://localhost:8000")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with tab3:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                    padding: 2rem; 
                    border-radius: 12px; 
                    margin-bottom: 2rem;
                    text-align: center;'>
            <h3 style='color: #333; margin-top: 0;'>🔍 Search Past Failures</h3>
            <p style='color: #666;'>Find similar failures from the knowledge base</p>
        </div>
    """, unsafe_allow_html=True)
    
    search_query = st.text_input(
        "Search Query", 
        placeholder="e.g., 'test failure', 'docker error', 'dependency issue'",
        label_visibility="visible"
    )
    search_limit = st.slider("Number of results", 1, 20, 5)
    
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not search_query or not search_query.strip():
            st.warning("⚠️ Please enter a search query.")
        else:
            with st.spinner("🔍 Searching for similar failures..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/search",
                        json={"query": search_query, "limit": search_limit},
                        timeout=30
                    )
                    if resp.status_code == 200:
                        results = resp.json()
                        if results.get("results"):
                            st.markdown(f"""
                                <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                                            padding: 1rem; 
                                            border-radius: 8px; 
                                            border-left: 4px solid #4caf50;
                                            margin: 1rem 0;
                                            text-align: center;'>
                                    <strong>✅ Found {results.get('count', 0)} similar failures</strong>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            for i, result in enumerate(results["results"], 1):
                                sev = result.get('severity', 'Unknown')
                                sev_colors = {
                                    "High": "#ff6b6b",
                                    "Medium": "#feca57",
                                    "Low": "#48dbfb"
                                }
                                sev_color = sev_colors.get(sev, "#95a5a6")
                                
                                with st.expander(f"Result {i}: {result.get('category', 'Unknown')} (Similarity: {result.get('similarity', 0):.3f})", expanded=False):
                                    st.markdown(f"""
                                        <div style='background: #f8f9fa; 
                                                    padding: 1rem; 
                                                    border-radius: 8px; 
                                                    margin: 0.5rem 0;
                                                    border-left: 4px solid {sev_color};'>
                                            <div style='margin-bottom: 0.5rem;'>
                                                <strong>Severity:</strong> 
                                                <span style='color: {sev_color}; font-weight: 600;'>{sev}</span>
                                            </div>
                                            <div style='margin-bottom: 0.5rem;'>
                                                <strong>Timestamp:</strong> {result.get('timestamp', 'Unknown')}
                                            </div>
                                            <div>
                                                <strong>Preview:</strong>
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    st.code(result.get('preview', ''), language='text')
                        else:
                            st.info("ℹ️ No similar failures found.")
                    else:
                        st.error(f"❌ Search failed: {resp.text}")
                except Exception as e:
                    st.error(f"❌ Search error: {e}")

# History section with modern styling
if st.session_state["history"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; 
                    border-radius: 12px; 
                    margin: 2rem 0 1rem 0;
                    text-align: center;'>
            <h2 style='color: white; margin: 0;'>📊 Analysis History</h2>
        </div>
    """, unsafe_allow_html=True)
    
    df = pd.DataFrame(st.session_state["history"])
    
    # Add filters in styled containers
    col1, col2 = st.columns(2)
    with col1:
        categories = ["All"] + list(df["Category"].unique())
        selected_category = st.selectbox("🔍 Filter by Category", categories)
    with col2:
        severities = ["All"] + list(df["Severity"].unique())
        selected_severity = st.selectbox("🔍 Filter by Severity", severities)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]
    if selected_severity != "All":
        filtered_df = filtered_df[filtered_df["Severity"] == selected_severity]
    
    # Styled dataframe
    st.dataframe(
        filtered_df, 
        use_container_width=True, 
        hide_index=True,
        height=400
    )
    
    if len(filtered_df) < len(df):
        st.markdown(f"""
            <div style='text-align: center; color: #666; margin-top: 1rem;'>
                Showing <strong>{len(filtered_df)}</strong> of <strong>{len(df)}</strong> results
            </div>
        """, unsafe_allow_html=True)
