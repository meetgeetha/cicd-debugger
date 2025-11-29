import requests
import streamlit as st
import pandas as pd

BACKEND_URL = "http://localhost:8000/analyze-log"

st.set_page_config(page_title="AI CI/CD Debugger", page_icon="🛠️", layout="centered")

st.title("🛠️ AI CI/CD Debugger")
st.write("Upload CI/CD logs to get automated failure diagnosis and fix suggestions.")

uploaded_file = st.file_uploader("📄 Upload CI Log", type=["txt", "log"])

if "history" not in st.session_state:
    st.session_state["history"] = []

if uploaded_file is not None:
    st.info("Click **Analyze Log** to send it to the backend.")

if uploaded_file is not None and st.button("Analyze Log"):
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    try:
        resp = requests.post(BACKEND_URL, files=files, timeout=90)
    except Exception as e:
        st.error(f"Failed to reach backend at {BACKEND_URL}: {e}")
    else:
        if resp.status_code != 200:
            st.error(f"Backend returned HTTP {resp.status_code}: {resp.text}")
        else:
            data = resp.json()

            st.subheader("🔍 Analysis Result")
            st.markdown(f"**Category:** {data.get('category', 'Unknown')}")

            sev = data.get("severity", "Medium")
            sev_display = {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}.get(sev, sev)
            st.markdown(f"**Severity:** {sev_display}")

            st.write("**Analysis:**")
            st.info(data.get("analysis", ""))

            st.write("**Suggested Fix:**")
            st.success(data.get("suggested_fix", ""))

            st.caption(
                f"Match Type: {data.get('match_type', 'LLM')} "
                f"| Similarity: {data.get('similarity', 'N/A')}"
            )

            st.session_state["history"].append(
                {
                    "Category": data.get("category", "Unknown"),
                    "Severity": data.get("severity", "Medium"),
                    "Match": data.get("match_type", "LLM"),
                }
            )

if st.session_state["history"]:
    st.subheader("📊 History")
    df = pd.DataFrame(st.session_state["history"])
    st.dataframe(df, use_container_width=True)
