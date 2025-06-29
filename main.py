import streamlit as st
from agent_system import ResearchAgent
from visualization import format_report
import time
import os
from dotenv import load_dotenv
import json


load_dotenv()


st.set_page_config(
    page_title="AI Research Agent", 
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .agent-card {
        background:linear-gradient(90deg, #fa709a 0%, #fee140 100%);
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .agent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .status-running {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .status-complete {
        background-color: #d1edff;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    .research-query {
        background: #f8f9ff;
        border: 2px solid #e6f2ff;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .sidebar-info {
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


required_keys = ["GROQ_API_KEY", "TAVILY_API_KEY"]
missing_keys = [key for key in required_keys if not os.getenv(key)]

if missing_keys:
    st.markdown("""
    <div style="background-color: #ffe6e6; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #ff4444;">
        <h3>⚠️ Configuration Required</h3>
        <p><strong>Missing environment variables:</strong> {}</p>
        <p>Please create a <code>.env</code> file in your project root with the required API keys.</p>
    </div>
    """.format(', '.join(missing_keys)), unsafe_allow_html=True)
    st.stop()


st.markdown("""
<div class="main-header">
    <h1>🧠 Multi-Agent Research System</h1>
    <p>By : Harshith Sanisetty • Advanced Research Pipeline • Real-time Analysis</p>
</div>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### ⚙️ Research Configuration")
    
    
    with st.expander("🔧 Advanced Settings", expanded=True):
        research_depth = st.selectbox(
            "Research Depth",
            ["Standard", "Deep", "Comprehensive"],
            index=0
        )
        
        include_sources = st.checkbox("Include Source Citations", value=True)
        real_time_update = st.checkbox("Real-time Updates", value=True)
    
   
    st.markdown("### 📊 System Status")
    st.markdown("""
    <div class="sidebar-info">
        <strong>🟢 APIs Connected</strong><br>
        • GROQ API: Active<br>
        • Tavily API: Active<br>
        • Agents: Ready
    </div>
    """, unsafe_allow_html=True)
    
    
    st.markdown("### 📚 Quick Templates")
    template_queries = {
        "Technology Comparison": "Compare Next.js vs SvelteKit for building real-time dashboard applications in 2024",
        "Market Analysis": "Analyze the current state of AI in healthcare industry 2024",
        "Research Summary": "Summarize recent developments in quantum computing applications",
        "Trend Analysis": "Identify emerging trends in sustainable technology"
    }
    
    selected_template = st.selectbox("Choose a template:", ["Custom"] + list(template_queries.keys()))


@st.cache_resource(show_spinner="🚀 Initializing AI agents...")
def get_agents():
    groq_key = os.getenv("GROQ_API_KEY")
    
    try:
        test_agent = ResearchAgent("researcher", groq_key)
        return {
            "researcher": test_agent,
            "critic": ResearchAgent("critic", groq_key),
            "synthesizer": ResearchAgent("synthesizer", groq_key)
        }
    except Exception as e:
        st.error(f"❌ Failed to initialize agents: {str(e)}")
        st.error("Please check your API keys and internet connection.")
        st.stop()


with st.spinner("Loading AI agents..."):
    agents = get_agents()


col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💭 Research Query")
    
    
    default_query = template_queries.get(selected_template, template_queries["Technology Comparison"]) if selected_template != "Custom" else ""
    
    query = st.text_area(
        "What would you like to research?",
        value=default_query,
        height=120,
        placeholder="Enter your research question here...",
        key="research_query"
    )

with col2:
    st.markdown("### 🎯 Agent Pipeline")
    st.markdown("""
    <div class="agent-card">
        <strong>🔍 Researcher</strong><br>
        <small>Gathers comprehensive data</small>
    </div>
    <div class="agent-card">
        <strong>🧐 Critic</strong><br>
        <small>Analyzes and validates claims</small>
    </div>
    <div class="agent-card">
        <strong>✍️ Synthesizer</strong><br>
        <small>Creates final report</small>
    </div>
    """, unsafe_allow_html=True)


st.markdown("---")


if st.button("🚀 Start Research", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("⚠️ Please enter a research query to proceed.")
        st.stop()
    
    
    progress_col1, progress_col2, progress_col3 = st.columns(3)
    
    
    progress_bar = st.progress(0)
    status_placeholder = st.empty()
    
    
    research_container = st.container()
    critique_container = st.container()
    synthesis_container = st.container()
    
    try:
        
        with progress_col1:
            st.markdown('<div class="status-badge status-running">🔍 Researching...</div>', unsafe_allow_html=True)
        
        status_placeholder.info("🔍 **Phase 1/3:** Researcher Agent is gathering comprehensive data...")
        progress_bar.progress(10)
        
        research = agents["researcher"].run({"input": query})
        progress_bar.progress(33)
        
        with progress_col1:
            st.markdown('<div class="status-badge status-complete">✅ Research Complete</div>', unsafe_allow_html=True)
        
        
        with progress_col2:
            st.markdown('<div class="status-badge status-running">🧐 Analyzing...</div>', unsafe_allow_html=True)
        
        status_placeholder.info("🧐 **Phase 2/3:** Critic Agent is analyzing claims and validating data...")
        
        critique = agents["critic"].run({"input": f"Analyze this research: {research}"})
        progress_bar.progress(66)
        
        with progress_col2:
            st.markdown('<div class="status-badge status-complete">✅ Analysis Complete</div>', unsafe_allow_html=True)
        
        
        with progress_col3:
            st.markdown('<div class="status-badge status-running">✍️ Synthesizing...</div>', unsafe_allow_html=True)
        
        status_placeholder.info("✍️ **Phase 3/3:** Synthesizer Agent is creating comprehensive report...")
        
        synthesis = agents["synthesizer"].run({
            "input": f"Create final report based on research: {research} and critique: {critique}"
        })
        progress_bar.progress(100)
        
        with progress_col3:
            st.markdown('<div class="status-badge status-complete">✅ Synthesis Complete</div>', unsafe_allow_html=True)
        
        status_placeholder.success("🎉 **Research Pipeline Complete!** All agents have finished processing.")
        
        
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Final Report", "📊 Research Data", "🔍 Critical Analysis", "⚙️ Process Details"])
        
        with tab1:
            st.markdown("### 📋 Comprehensive Research Report")
            
            
            verification_data = agents["researcher"].claim_tracker.get_verification_report()
            
            
            formatted_report = format_report(research, critique, synthesis, verification_data)
            st.markdown(formatted_report, unsafe_allow_html=True)
            
            
            st.download_button(
                label="📥 Download Report",
                data=formatted_report,
                file_name=f"research_report_{int(time.time())}.html",
                mime="text/html"
            )
        
        with tab2:
            st.markdown("### 📊 Raw Research Data")
            with st.expander("View detailed research findings", expanded=True):
                st.markdown(research)
        
        with tab3:
            st.markdown("### 🔍 Critical Analysis")
            with st.expander("View critical evaluation", expanded=True):
                st.markdown(critique)
        
        with tab4:
            st.markdown("### ⚙️ Synthesis Process")
            with st.expander("View synthesis details", expanded=True):
                st.markdown(synthesis)
            
            
            if verification_data:
                st.markdown("### 📈 Verification Metrics")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Claims Verified", len(verification_data.get('verified_claims', [])))
                with col2:
                    st.metric("Sources Cited", len(verification_data.get('sources', [])))
                with col3:
                    st.metric("Confidence Score", f"{verification_data.get('confidence', 0):.1%}")
    
    except Exception as e:
        st.error(f"❌ **Research Error:** {str(e)}")
        st.error("Please try again or check your configuration.")


st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🧠 <strong>Multi-Agent Research System</strong> </p>
    <p><small>Real-time research • Critical analysis • Comprehensive reporting</small></p>
</div>
""", unsafe_allow_html=True)


import atexit
@atexit.register
def cleanup():
    for agent in agents.values():
        agent.close()