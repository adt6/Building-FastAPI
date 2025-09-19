"""
Streamlit Chatbot Interface for Clinical AI Assistant
A beautiful, professional interface for interacting with the clinical AI agent.
"""
import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Clinical AI Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .example-query {
        background-color: #f5f5f5;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
        cursor: pointer;
        border: 1px solid #ddd;
    }
    .example-query:hover {
        background-color: #e0e0e0;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-online {
        background-color: #4caf50;
    }
    .status-offline {
        background-color: #f44336;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "api_status" not in st.session_state:
        st.session_state.api_status = "unknown"
    if "agent_loading_attempted" not in st.session_state:
        st.session_state.agent_loading_attempted = False

def check_api_status():
    """Check if the FastAPI server is running."""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v2/health", timeout=3)
        if response.status_code == 200:
            st.session_state.api_status = "online"
            return True
        else:
            st.session_state.api_status = "offline"
            return False
    except:
        st.session_state.api_status = "offline"
        return False

def load_agent():
    """Load the AI agent."""
    try:
        if st.session_state.agent is None:
            with st.spinner("Loading AI agent..."):
                from agent.agent_factory import create_assistant
                st.session_state.agent = create_assistant()
                st.success("✅ AI agent loaded successfully!")
        return st.session_state.agent
    except Exception as e:
        st.error(f"❌ Failed to load AI agent: {str(e)}")
        st.error("Please check your configuration and try refreshing the page.")
        return None

def display_header():
    """Display the main header."""
    st.markdown('<h1 class="main-header">🏥 Clinical AI Assistant</h1>', unsafe_allow_html=True)
    
    # Add description
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; color: #666;">
        <p style="font-size: 1.1rem;">Intelligent healthcare data assistant powered by LangChain and Groq</p>
        <p style="font-size: 0.9rem;">Ask questions about patients, medical conditions, and encounters using natural language</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        api_online = check_api_status()
        status_color = "status-online" if api_online else "status-offline"
        status_text = "Online" if api_online else "Offline"
        st.markdown(f'<span class="status-indicator {status_color}"></span>**FastAPI Server:** {status_text}', unsafe_allow_html=True)
    
    with col2:
        agent_loaded = st.session_state.agent is not None
        status_color = "status-online" if agent_loaded else "status-offline"
        status_text = "Ready" if agent_loaded else "Not Loaded"
        st.markdown(f'<span class="status-indicator {status_color}"></span>**AI Agent:** {status_text}', unsafe_allow_html=True)
    
    with col3:
        groq_key = os.getenv("GROQ_API_KEY")
        status_color = "status-online" if groq_key and groq_key != "your-groq-api-key-here" else "status-offline"
        status_text = "Configured" if groq_key and groq_key != "your-groq-api-key-here" else "Not Set"
        st.markdown(f'<span class="status-indicator {status_color}"></span>**Groq API:** {status_text}', unsafe_allow_html=True)
    
    # Add manual agent loading button if agent is not loaded
    if st.session_state.agent is None:
        st.warning("⚠️ AI Agent not loaded. Click the button below to load it manually.")
        if st.button("🤖 Load AI Agent", use_container_width=True):
            load_agent()
            st.rerun()
    
    # Quick stats
    if api_online and agent_loaded:
        st.success("✅ System Ready! You can start asking questions about patients and medical data.")

def display_sidebar():
    """Display the sidebar with examples and information."""
    with st.sidebar:
        st.header("📋 Quick Examples")
        
        # Patient Information Examples
        st.subheader("👤 Patient Information")
        patient_examples = [
            "Get patient information for patient ID 2",
            "Get patient information for patient ID 3", 
            "Search for patients named Robert854",
            "Search for patients with first name Maxwell",
            "Get a complete patient summary for patient 4"
        ]
        
        for query in patient_examples:
            if st.button(f"💬 {query}", key=f"patient_{query}", use_container_width=True):
                st.session_state.user_input = query
                st.rerun()
        
        # Medical Conditions Examples
        st.subheader("🏥 Medical Conditions")
        condition_examples = [
            "What conditions does patient 2 have?",
            "Show me all medical conditions for patient 3",
            "Get patient conditions for patient ID 4"
        ]
        
        for query in condition_examples:
            if st.button(f"💬 {query}", key=f"condition_{query}", use_container_width=True):
                st.session_state.user_input = query
                st.rerun()
        
        # Medical Encounters Examples
        st.subheader("📅 Medical Encounters")
        encounter_examples = [
            "Show me all encounters for patient 2",
            "Get patient encounters for patient ID 3",
            "What encounters has patient 4 had?"
        ]
        
        for query in encounter_examples:
            if st.button(f"💬 {query}", key=f"encounter_{query}", use_container_width=True):
                st.session_state.user_input = query
                st.rerun()
        
        st.divider()
        
        st.header("🛠️ Available Tools")
        
        # Patient Tools
        with st.expander("👤 Patient Tools", expanded=True):
            st.markdown("""
            **🔍 Search & Find:**
            - `search_patients()` - Find patients by name, demographics
            - `get_patient_info()` - Get basic patient details
            
            **📊 Patient Data:**
            - `get_patient_conditions()` - Medical conditions
            - `get_patient_encounters()` - Medical encounters  
            - `get_patient_summary()` - Complete overview
            """)
        
        # Tool Examples
        with st.expander("💡 Tool Usage Examples"):
            st.markdown("""
            **Search by Name:**
            - "Search for patients named Robert854"
            - "Find patients with first name Maxwell"
            
            **Get Patient Data:**
            - "Get patient information for patient ID 2"
            - "What conditions does patient 3 have?"
            - "Show me encounters for patient 4"
            
            **Complete Summary:**
            - "Get a complete patient summary for patient 2"
            """)
        
        # Data Insights
        with st.expander("📈 Data Insights"):
            st.markdown("""
            **Current Database:**
            - Multiple patients with unique IDs
            - Medical conditions (sinusitis, hypertension, etc.)
            - Medical encounters (AMB type)
            - Patient demographics and contact info
            
            **Sample Patient IDs:**
            - Patient 2: Zula72 Ondricka197
            - Patient 3: Robert854 Botsford977  
            - Patient 4: Will178 Lang846
            """)
        
        st.divider()
        
        st.header("ℹ️ How to Use")
        st.markdown("""
        **🚀 Getting Started:**
        1. **FastAPI Server** must be running on port 8000
        2. **AI Agent** loads automatically on first query
        3. **Use natural language** - ask questions naturally
        4. **Click examples** in sidebar for quick queries
        
        **💬 Example Queries:**
        - "Get patient information for patient ID 2"
        - "Search for patients named Robert854"
        - "What conditions does patient 3 have?"
        - "Show me all encounters for patient 4"
        
        **🔧 Troubleshooting:**
        - Check FastAPI server status (green = online)
        - Click "Load AI Agent" if agent shows offline
        - Use "Test Agent Loading" for debugging
        """)
        
        st.divider()
        
        st.header("🐛 Debug Info")
        if st.button("🔍 Test Agent Loading", use_container_width=True):
            try:
                with st.spinner("Testing agent loading..."):
                    from agent.agent_factory import create_assistant
                    test_agent = create_assistant()
                    st.success("✅ Agent test successful!")
                    st.json({"agent_type": str(type(test_agent))})
            except Exception as e:
                st.error(f"❌ Agent test failed: {str(e)}")
                st.code(str(e))

def display_chat_history():
    """Display the chat history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Check if the message contains HTML formatting
            if "<div style=" in message["content"] or "<h3" in message["content"] or "<h4" in message["content"]:
                st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

def handle_user_input():
    """Handle user input and generate AI response."""
    if prompt := st.chat_input("Ask me about patients, encounters, or any clinical data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    agent = load_agent()
                    if agent:
                        response = agent.invoke({"input": prompt})
                        ai_response = response['output']
                    else:
                        ai_response = "❌ AI agent is not available. Please check the configuration."
                except Exception as e:
                    ai_response = f"❌ Error: {str(e)}"
            
            # Check if the response contains HTML formatting
            if "<div style=" in ai_response or "<h3" in ai_response or "<h4" in ai_response:
                st.markdown(ai_response, unsafe_allow_html=True)
            else:
                st.markdown(ai_response)
        
        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

def main():
    """Main application function."""
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display sidebar
    display_sidebar()
    
    # Check if user input is set from example button
    if hasattr(st.session_state, 'user_input'):
        prompt = st.session_state.user_input
        delattr(st.session_state, 'user_input')
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    agent = load_agent()
                    if agent:
                        response = agent.invoke({"input": prompt})
                        ai_response = response['output']
                    else:
                        ai_response = "❌ AI agent is not available. Please check the configuration."
                except Exception as e:
                    ai_response = f"❌ Error: {str(e)}"
            
            # Check if the response contains HTML formatting
            if "<div style=" in ai_response or "<h3" in ai_response or "<h4" in ai_response:
                st.markdown(ai_response, unsafe_allow_html=True)
            else:
                st.markdown(ai_response)
        
        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Display chat history
    display_chat_history()
    
    # Handle new user input
    handle_user_input()
    
    # Add clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()
