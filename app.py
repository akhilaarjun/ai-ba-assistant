import streamlit as st
from ba_engine import BAEngine

# Page Config
st.set_page_config(
    page_title="Agile Requirement Engineering Assistant",
    page_icon="💼",
    layout="wide"
)

# App Title 
st.title("💼 Enterprise Requirement Engineering Assistant")
st.markdown("Transform unstructured stakeholder transcripts into structured User Stories, Gherkin Criteria, and Jira-ready exports.")

# Sidebar for Configuration and Portfolio Notes
with st.sidebar:
    st.header("⚙️ Configuration")
    
  # Show input box EMPTY by default so visitors never see your key
    user_pasted_key = st.text_input(
        "Gemini API Key (Optional):", 
        type="password", 
        help="Leave blank to use default portfolio key, or enter your own free key from Google AI Studio."
    )
    
    # Priority: 1. User pasted key -> 2. Streamlit Secrets key -> 3. Blank
    api_key = user_pasted_key if user_pasted_key.strip() else st.secrets.get("GEMINI_API_KEY", "")
    
    st.caption("Get a free key at [aistudio.google.com](https://aistudio.google.com/)")
    
    st.markdown("---")
    st.markdown("### 📌 Capabilities")
    st.markdown("- **LLM Requirement Parsing**")
    st.markdown("- **INVEST Quality Score Audit**")
    st.markdown("- **BDD / Gherkin Extraction**")
    st.markdown("- **Jira & Azure DevOps CSV Export**")

# Sample Prompts for Testing
sample_scenarios = {
    "Select a Sample Scenario...": "",
    "🏥 Healthcare Portal": "Patients are complaining that they can't view lab results online. Doctors need to publish PDF reports when reviewed, and patients should receive email alerts.",
    "💳 FinTech Payments": "Checkout drop-offs are high because we only support credit cards. We need Apple Pay and Google Pay support, plus automated daily reconciliation reports for finance.",
    "🚚 Logistics & Fleet": "Warehouse managers are losing track of delayed shipments. We need a tracking dashboard highlighting orders stuck >48 hours and mobile photo proof of delivery for drivers."
}

selected_sample = st.selectbox("💡 Quick Test Scenarios:", list(sample_scenarios.keys()))
default_text = sample_scenarios[selected_sample] if selected_sample != "Select a Sample Scenario..." else ""


raw_notes = st.text_area(
    "Paste Stakeholder Notes, Email, or Meeting Transcript:",
    value=default_text,
    height=180,
    placeholder="Example: Tenants keep calling about repair status. We need a Power BI dashboard for repair teams and SMS notifications for tenants..."
)

if st.button("🚀 Process Requirements", type="primary"):
    if not api_key:
        st.error("Please enter a Gemini API key in the sidebar to proceed.")
    elif not raw_notes.strip():
        st.warning("Please enter some text or select a sample scenario above.")
    else:
        try:
            with st.spinner("Analyzing requirements & auditing agile quality metrics..."):
                engine = BAEngine(api_key)
                requirements = engine.generate_requirements(raw_notes)
                audit = engine.audit_requirements(requirements)
                df = engine.to_pandas_df(requirements)

            st.success("Analysis Complete!")

            # Quality Metric Display
            score = audit.get("invest_score", 0)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric(label="INVEST Quality Score", value=f"{score}/100")
            with col2:
                if "strengths" in audit:
                    st.write("**Strengths:** " + ", ".join(audit.get("strengths", [])))
                if "areas_for_improvement" in audit:
                    st.write("**Areas for Improvement:** " + ", ".join(audit.get("areas_for_improvement", [])))

            st.divider()

            # Interactive Output Tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 User Stories", 
                "🥒 Acceptance Criteria", 
                "💻 Technical & Data Specs", 
                "📊 Jira CSV Export"
            ])

            with tab1:
                st.subheader("User Stories")
                for story in requirements.get("user_stories", []):
                    story_id = story.get("id", "US")
                    # Safe story text retrieval with fallback formatting
                    story_text = story.get("full_story") or f"As a {story.get('role', 'user')}, I want to {story.get('action', '')}, so that {story.get('benefit', '')}."
                    st.info(f"**[{story_id}]** {story_text}")

            with tab2:
                st.subheader("Gherkin Acceptance Criteria")
                for ac in requirements.get("acceptance_criteria", []):
                    story_ref = ac.get('story_id', 'US')
                    gherkin_code = ac.get('gherkin', 'N/A')
                    st.markdown(f"**Story Reference:** `{story_ref}`")
                    st.code(gherkin_code, language="gherkin")

            with tab3:
                st.subheader("Technical & Non-Functional Specifications")
                for note in requirements.get("data_and_tech_notes", []):
                    st.write(f"• {note}")

            with tab4:
                st.subheader("Jira / Azure DevOps Import Preview")
                st.dataframe(df, use_container_width=True)
                
                # CSV Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV for Jira Import",
                    data=csv,
                    file_name="jira_user_stories.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error processing request: {e}")
