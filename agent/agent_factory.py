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


def get_llm():
    """
    Create and configure the LLM (Language Model) based on DEFAULT_LLM_TYPE.
    This is the "brain" of our AI assistant.
    """
    # Choose model based on DEFAULT_LLM_TYPE from config
    if agent_config.DEFAULT_LLM_TYPE == agent_config.OPENAI_LLM_TYPE:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
        
        return ChatOpenAI(
            model=agent_config.MODEL_ID_OPENAI,  # gpt-4o-mini
            temperature=0.1,
            api_key=api_key
        )
    
    elif agent_config.DEFAULT_LLM_TYPE == agent_config.SONNET_LLM_TYPE:
        # TODO: Add Anthropic Claude Sonnet support
        raise NotImplementedError("Anthropic Claude Sonnet not implemented yet. Please use OPENAI_LLM_TYPE for now.")
    
    elif agent_config.DEFAULT_LLM_TYPE == agent_config.LLAMA_GROQ_LLM_TYPE:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Please set GROQ_API_KEY environment variable.")
        
        return ChatGroq(
            model=agent_config.MODEL_ID_LLAMA_GROQ,  # llama3-70b-8192
            temperature=0.1,
            api_key=api_key
        )
    
    elif agent_config.DEFAULT_LLM_TYPE == agent_config.MIXTRAL_LLM_TYPE:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Please set GROQ_API_KEY environment variable.")
        
        return ChatGroq(
            model=agent_config.MODEL_ID_MIXTRAL_GROQ,  # mixtral-8x7b-32768
            temperature=0.1,
            api_key=api_key
        )
    
    elif agent_config.DEFAULT_LLM_TYPE == agent_config.HAIKU_LLM_TYPE:
        # TODO: Add Anthropic Claude Haiku support
        raise NotImplementedError("Anthropic Claude Haiku not implemented yet. Please use MIXTRAL_LLM_TYPE for now.")
    
    else:
        raise ValueError(f"Unknown LLM type: {agent_config.DEFAULT_LLM_TYPE}. Please check agent_config.py")


def create_assistant() -> AgentExecutor:
    """
    Main factory method - creates a fully configured AI assistant.
    This combines all components: instructions, LLM, tools, and prompts.
    """
    # Step 1: Load instructions (how the AI should behave)
    instructions = load_and_format_instructions()
    
    # Step 2: Create LLM (the AI brain)
    llm = get_llm()
    
    # Step 3: Get tools (functions to call your API)
    from .tools.patient_tools import (
        get_patient_info,
        search_patients,
        get_patient_conditions,
        get_patient_encounters,
        get_patient_summary
    )
    
    tools = [
        get_patient_info,
        search_patients,
        get_patient_conditions,
        get_patient_encounters,
        get_patient_summary
    ]
    
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
    
    # Update the prompt template with our clinical instructions
    prompt.template = clinical_instructions + prompt.template
    
    # Step 5: Create the agent (combines LLM + tools + prompt)
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    # Step 6: Create agent executor (handles the conversation flow)
    #agent_executor is essentially a conversational AI interface that you can ask questions to, and it will use your healthcare API tools to find answers!
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,           # Show thinking process
        max_iterations=5,       # Max steps to answer
        early_stopping_method="generate",
        handle_parsing_errors=True  # Handle output parsing errors gracefully
    )
    
    return agent_executor
