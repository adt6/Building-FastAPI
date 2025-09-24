"""
Agent Factory for creating configured clinical AI assistants.
This combines all components to create a working AI assistant.
"""
import os
from pathlib import Path
from datetime import datetime
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory

from . import agent_config


def load_and_format_instructions() -> str:
    """
    Load instructions from file or use fallback.
    This tells the AI how to behave as a clinical assistant.
    """
    if agent_config.INSTRUCTIONS_FILE_PATH.exists():
        with open(agent_config.INSTRUCTIONS_FILE_PATH, 'r') as f:
            instructions = f.read()
    else:
        instructions = agent_config.FALLBACK_INSTRUCTIONS
    
    # Replace placeholders with current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    instructions = instructions.replace("{{CURRENT_DATE}}", current_date)
    
    return instructions


def get_llm(model_type=None):
    """
    Create and configure the LLM (Language Model) based on model_type or DEFAULT_LLM_TYPE.
    This is the "brain" of our AI assistant.
    
    Args:
        model_type (str, optional): The type of model to use. If None, uses DEFAULT_LLM_TYPE.
    """
    # Use provided model_type or fall back to DEFAULT_LLM_TYPE
    selected_model_type = model_type or agent_config.DEFAULT_LLM_TYPE
    
    # Choose model based on selected model type
    if selected_model_type == agent_config.OPENAI_LLM_TYPE:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
        
        return ChatOpenAI(
            model=agent_config.MODEL_ID_OPENAI,  # gpt-4o-mini
            temperature=0.1,
            api_key=api_key
        )
    
    elif selected_model_type == agent_config.SONNET_LLM_TYPE:
        # TODO: Add Anthropic Claude Sonnet support
        raise NotImplementedError("Anthropic Claude Sonnet not implemented yet. Please use OPENAI_LLM_TYPE for now.")
    
    elif selected_model_type == agent_config.LLAMA_GROQ_LLM_TYPE:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Please set GROQ_API_KEY environment variable.")
        
        return ChatGroq(
            model=agent_config.MODEL_ID_LLAMA_GROQ,  # llama3-70b-8192
            temperature=0.1,
            api_key=api_key
        )
    
    elif selected_model_type == agent_config.MIXTRAL_LLM_TYPE:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Please set GROQ_API_KEY environment variable.")
        
        return ChatGroq(
            model=agent_config.MODEL_ID_MIXTRAL_GROQ,  # mixtral-8x7b-32768
            temperature=0.1,
            api_key=api_key
        )
    
    elif selected_model_type == agent_config.HAIKU_LLM_TYPE:
        # TODO: Add Anthropic Claude Haiku support
        raise NotImplementedError("Anthropic Claude Haiku not implemented yet. Please use MIXTRAL_LLM_TYPE for now.")
    
    elif selected_model_type == agent_config.GEMINI_LLM_TYPE:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Please set GEMINI_API_KEY environment variable.")
        
        import sys
        print(f"\n🤖 DEBUG: Creating Gemini LLM with model: {agent_config.MODEL_ID_GEMINI}", file=sys.stderr)
        
        # Import ChatGoogleGenerativeAI for Gemini support
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            print("✅ DEBUG: Successfully imported ChatGoogleGenerativeAI", file=sys.stderr)
        except ImportError:
            raise ImportError("Please install langchain-google-genai: pip install langchain-google-genai")
        
        llm = ChatGoogleGenerativeAI(
            model=agent_config.MODEL_ID_GEMINI,  # gemini-2.5-flash
            temperature=0.1,
            google_api_key=api_key
        )
        
        print(f"✅ DEBUG: Gemini LLM created successfully\n", file=sys.stderr)
        return llm
    
    else:
        raise ValueError(f"Unknown LLM type: {selected_model_type}. Please check agent_config.py")


def create_assistant(model_type=None) -> AgentExecutor:
    """
    Main factory method - creates a fully configured AI assistant.
    This combines all components: instructions, LLM, tools, and prompts.
    
    Args:
        model_type (str, optional): The type of model to use. If None, uses DEFAULT_LLM_TYPE.
    """
    # Step 1: Load instructions (how the AI should behave)
    instructions = load_and_format_instructions()
    
    # Step 2: Create LLM (the AI brain)
    llm = get_llm(model_type)
    
    # Step 3: Get tools (functions to call your API)
    from .tools.patient_tools import (
        get_patient_info,
        search_patients,
        get_patient_conditions,
        get_patient_encounters,
        get_patient_observations,
        get_patient_summary
    )
    
    tools = [
        get_patient_info,
        search_patients,
        get_patient_conditions,
        get_patient_encounters,
        get_patient_observations,
        get_patient_summary
    ]
    
    import sys
    print(f"🛠️ DEBUG: Loaded {len(tools)} tools for agent", file=sys.stderr)
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool.name}: {tool.description[:50]}...", file=sys.stderr)
    
    # Step 4: Create prompt template (how to format conversations)
    # Use the standard ReAct prompt template
    prompt = hub.pull("hwchase17/react")
    
    # Add our clinical instructions to the prompt
    clinical_instructions = f"""
{instructions}

You are a clinical AI assistant that helps healthcare professionals access patient information.
Use the available tools to retrieve and format patient data in a professional, clinical manner.

CRITICAL INSTRUCTION: When you receive patient information from tools, you MUST ALWAYS 
provide a natural, conversational summary in paragraph form. NEVER display the raw 
structured data with headers like "PATIENT INFORMATION" or "CONTACT INFORMATION". 

Instead, write a flowing summary like: "John Doe is a 45-year-old male patient with ID 123..."

ALWAYS summarize patient data in natural language - this is mandatory for all patient queries.

MEMORY INSTRUCTIONS:
- You have access to conversation history to understand context
- Use previous messages to understand follow-up questions
- If a user asks "What are their conditions?" after discussing a patient, you know which patient they mean
- Maintain context throughout the conversation

IMPORTANT SEARCH GUIDELINES:
- When searching for patients by name, if given a single name like "Robert854", use ONLY the first_name parameter
- Do NOT split single names into first_name and last_name unless explicitly told to do so
- For single names, use: search_patients(first_name="Robert854")
- Only use both first_name and last_name when the user explicitly provides both parts
- CRITICAL: When calling tools, pass parameter values correctly:
  * Use first_name="Maxwell782" NOT first_name="first_name=Maxwell782"
  * Use first_name="Robert854", last_name="Botsford977" NOT first_name="first_name=Robert854, last_name=Botsford977"
  * Each parameter should be passed separately, not concatenated into one string
- For patient tools, use: patient_identifier=2 NOT patient_identifier="2" (avoid quotes around numbers)

"""
    
    # Update the prompt template with our clinical instructions and memory
    prompt.template = clinical_instructions + prompt.template
    
    # Add chat history to the prompt template
    if "chat_history" not in prompt.template:
        prompt.template = prompt.template.replace(
            "{input}", 
            "Previous conversation:\n{chat_history}\n\nCurrent question: {input}"
        )
    
    # Step 5: Create conversation memory
    print(f"🧠 DEBUG: Creating conversation memory", file=sys.stderr)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )
    print(f"🧠 DEBUG: Memory created with key: chat_history", file=sys.stderr)
    
    # Step 6: Create the agent (combines LLM + tools + prompt)
    print(f"🤖 DEBUG: Creating ReAct agent with {model_type or 'default'} model", file=sys.stderr)
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    # Step 7: Create agent executor (handles the conversation flow)
    #agent_executor is essentially a conversational AI interface that you can ask questions to, and it will use your healthcare API tools to find answers!
    print(f"🔄 DEBUG: Creating AgentExecutor with memory and verbose=True", file=sys.stderr)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,          # Add conversation memory
        verbose=True,           # Show thinking process
        max_iterations=20,      # Max steps to answer (increased for complex queries)
        handle_parsing_errors=True,  # Handle output parsing errors gracefully
        return_intermediate_steps=True  # Return intermediate steps for debugging
    )
    print(f"✅ DEBUG: AgentExecutor created successfully", file=sys.stderr)
    return agent_executor
