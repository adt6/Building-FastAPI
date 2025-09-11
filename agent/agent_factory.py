"""
Agent Factory for creating configured clinical AI assistants.
This combines all components to create a working AI assistant.
"""
import os
from pathlib import Path
from datetime import datetime
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

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
    
    elif agent_config.DEFAULT_LLM_TYPE == agent_config.HAIKU_LLM_TYPE:
        # TODO: Add Anthropic Claude Haiku support
        raise NotImplementedError("Anthropic Claude Haiku not implemented yet. Please use OPENAI_LLM_TYPE for now.")
    
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
    # TODO: We'll add this later
    tools = []  # For now, no tools
    
    # Step 4: Create prompt template (how to format conversations)
    prompt = PromptTemplate.from_template("""
{instructions}

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")
    
    # Step 5: Create the agent (combines LLM + tools + prompt)
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    # Step 6: Create agent executor (handles the conversation flow)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,           # Show thinking process
        max_iterations=5,       # Max steps to answer
        early_stopping_method="generate"
    )
    
    return agent_executor
