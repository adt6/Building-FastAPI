"""
Streamlit Chatbot Interface for Clinical AI Assistant
A beautiful, professional interface for interacting with the clinical AI agent.
"""
import streamlit as st
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Import agent configuration
from agent import agent_config

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
    .status-loading {
        background-color: #ff9800;
        animation: pulse 1.5s ease-in-out infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
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
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = None

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

def load_agent(model_type=None):
    """Load the AI agent with specified model type."""
    try:
        # Use the model_type parameter or fall back to session state
        effective_model_type = model_type or st.session_state.get('selected_model', None)
        
        # If no model is specified and none is in session state, don't load anything
        if effective_model_type is None:
            return None
        
        # Check if we need to reload the agent (different model type)
        current_model = st.session_state.get('selected_model', None)
        if st.session_state.agent is None or current_model != effective_model_type:
            import sys
            print(f"🔄 STREAMLIT: Loading agent with model: {effective_model_type}", file=sys.stderr)
            print(f"🔄 STREAMLIT: Previous model was: {current_model}", file=sys.stderr)
            
            with st.spinner(f"Loading AI agent with {effective_model_type or 'default'} model..."):
                from agent.agent_factory import create_assistant
                st.session_state.agent = create_assistant(effective_model_type)
                st.session_state.selected_model = effective_model_type
                st.success(f"✅ AI agent loaded successfully with {effective_model_type or 'default'} model!")
        return st.session_state.agent
    except Exception as e:
        import sys
        print(f"❌ STREAMLIT: Failed to load agent: {str(e)}", file=sys.stderr)
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
        # More reliable agent status check
        agent_loaded = st.session_state.agent is not None
        selected_model = st.session_state.get('selected_model', None)
        
        # If we have a selected model but no agent, it means we're in the process of loading
        if selected_model and not agent_loaded:
            status_color = "status-loading"
            model_display_names = {
                "gemini": "Gemini 2.5 Flash",
                "llama_groq": "Llama 3.3 70B",
                "mixtral": "Mistral Saba 24B", 
                "openai": "GPT-4o Mini"
            }
            model_name = model_display_names.get(selected_model, selected_model)
            status_text = f"Loading ({model_name})..."
        elif agent_loaded and selected_model:
            status_color = "status-online"
            model_display_names = {
                "gemini": "Gemini 2.5 Flash",
                "llama_groq": "Llama 3.3 70B",
                "mixtral": "Mistral Saba 24B", 
                "openai": "GPT-4o Mini"
            }
            model_name = model_display_names.get(selected_model, selected_model)
            status_text = f"Ready ({model_name})"
        else:
            status_color = "status-offline"
            status_text = "Not Loaded"
            
        st.markdown(f'<span class="status-indicator {status_color}"></span>**AI Agent:** {status_text}', unsafe_allow_html=True)
    
    with col3:
        groq_key = os.getenv("GROQ_API_KEY")
        status_color = "status-online" if groq_key and groq_key != "your-groq-api-key-here" else "status-offline"
        status_text = "Configured" if groq_key and groq_key != "your-groq-api-key-here" else "Not Set"
        st.markdown(f'<span class="status-indicator {status_color}"></span>**Groq API:** {status_text}', unsafe_allow_html=True)
    
    # Show message if no model is selected
    if st.session_state.get('selected_model') is None:
        st.info("💡 Please select an AI model from the sidebar to get started.")
    
    # Quick stats
    if api_online and agent_loaded:
        st.success("✅ System Ready! You can start asking questions about patients and medical data.")

def display_sidebar():
    """Display the sidebar with examples and information."""
    with st.sidebar:
        # Model Selection
        st.header("🤖 AI Model Selection")
        
        # Import agent config for model options
        from agent import agent_config
        
        model_options = {
            "Llama 3.3 70B (Groq)": agent_config.LLAMA_GROQ_LLM_TYPE,
            "Mistral Saba 24B (Groq)": agent_config.MIXTRAL_LLM_TYPE,
            "Gemini 2.5 Flash (Free)": agent_config.GEMINI_LLM_TYPE,
            "GPT-4o Mini (OpenAI)": agent_config.OPENAI_LLM_TYPE,
        }
        
        # Get current model (no default)
        current_model = st.session_state.get('selected_model', None)
        
        # Find the display name for current model
        current_display = None
        if current_model:
            for display_name, model_type in model_options.items():
                if model_type == current_model:
                    current_display = display_name
                    break
        
        # Add a placeholder option for no selection
        options_with_none = ["Select a model..."] + list(model_options.keys())
        
        # Determine the index
        if current_display:
            index = options_with_none.index(current_display)
        else:
            index = 0  # "Select a model..." option
        
        selected_display = st.selectbox(
            "Choose AI Model:",
            options=options_with_none,
            index=index,
            help="Select which AI model to use for responses. Gemini is free!"
        )
        
        # Handle the selection
        if selected_display == "Select a model...":
            selected_model_type = None
            # Clear the agent if a model was previously selected
            if current_model:
                st.session_state.agent = None
                st.session_state.selected_model = None
        else:
            selected_model_type = model_options[selected_display]
            
            # If model changed, reload agent
            if selected_model_type != current_model:
                st.session_state.agent = None  # Force reload
                st.session_state.selected_model = selected_model_type
                # Automatically load the agent when model is selected
                load_agent(selected_model_type)
        
        st.divider()
        
        # Reset button
        if st.button("🔄 Reset to Default", use_container_width=True, help="Clear all selections and start fresh"):
            st.session_state.selected_model = None
            st.session_state.agent = None
            st.rerun()
        
        st.divider()
        
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
                # Process the example directly
                process_message(query)
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
                # Process the example directly
                process_message(query)
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
                # Process the example directly
                process_message(query)
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

def process_message(prompt):
    """Process a user message and generate AI response."""
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate AI response
    with st.spinner("Thinking..."):
        try:
            # Get the current model, but don't reset it if it's None
            current_model = st.session_state.get('selected_model', None)
            if current_model is None:
                # If no model is selected, use the default
                current_model = agent_config.DEFAULT_LLM_TYPE
                st.session_state.selected_model = current_model
            agent = load_agent(current_model)
            if agent:
                import sys
                print(f"🤖 STREAMLIT: Invoking agent with prompt: {prompt[:50]}...", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                print("🤖 AGENT THINKING PROCESS:", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                response = agent.invoke({"input": prompt})
                print("=" * 80, file=sys.stderr)
                print("✅ AGENT THINKING COMPLETE", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                
                # Show intermediate steps if available
                if 'intermediate_steps' in response:
                    print(f"🔍 INTERMEDIATE STEPS: {len(response['intermediate_steps'])} steps", file=sys.stderr)
                    for i, step in enumerate(response['intermediate_steps']):
                        action, observation = step
                        print(f"  Step {i+1}:", file=sys.stderr)
                        print(f"    🤔 Thought: {action.log.split('Action:')[0].strip()}", file=sys.stderr)
                        print(f"    🛠️  Action: {action.tool}", file=sys.stderr)
                        print(f"    📝 Input: {action.tool_input}", file=sys.stderr)
                        print(f"    👀 Observation: {observation[:100]}...", file=sys.stderr)
                
                ai_response = response['output']
                print(f"✅ STREAMLIT: Agent response received", file=sys.stderr)
            else:
                ai_response = "❌ AI agent is not available. Please check the configuration."
        except Exception as e:
            # Check if it's an iteration limit error but we still got a response
            if "iteration limit" in str(e).lower() or "time limit" in str(e).lower():
                # The agent might have generated a response before hitting the limit
                ai_response = f"⚠️ Response was cut off due to complexity. The agent was processing your request but hit the iteration limit. Please try breaking your question into smaller parts.\n\nError details: {str(e)}"
            else:
                ai_response = f"❌ Error: {str(e)}"
        
    # Add AI response to chat history
    st.session_state.messages.append({"role": "assistant", "content": ai_response})


def main():
    """Main application function."""
    initialize_session_state()
    
    # Display sidebar first (contains model selection and load button)
    display_sidebar()
    
    # Display header (now shows correct status after sidebar processing)
    display_header()
    
    # Display chat history
    display_chat_history()
    
    # Always show the input box
    placeholder = "Ask me about patients, encounters, or any clinical data..."
    
    if prompt := st.chat_input(placeholder):
        process_message(prompt)
        st.rerun()
    
    # Add clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()
