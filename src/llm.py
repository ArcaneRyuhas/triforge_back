import os
import json
import tempfile
import re
import asyncio
from fastapi import FastAPI, Request, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, List, Optional
from pydantic import BaseModel
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain, LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from uuid import uuid4

# API key setup
load_dotenv()

api_key = os.getenv("GENAI_API_KEY")
if not api_key:
    raise ValueError("No API_KEY found. Ensure you have a .env file with GENAI_API_KEY defined")

# Configure Gemini
genai.configure(api_key=api_key)

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    user_id: str
    content: str
    agent_type: Optional[str] = "general"  # 'general', 'documentation', 'diagram', or 'code'
    diagram_format: Optional[str] = None
    programming_language: Optional[str] = None

class DocumentationRequest(BaseModel):
    requirement: str
    document_format: str = "Jira Stories"
    user_id: Optional[str] = None
    agent_type: Optional[str] = "documentation"

class ModifyJiraStoriesRequest(BaseModel):
    user_id: str
    modification_prompt: str
    original_stories: Optional[str] = None 
    agent_type: Optional[str] = "documentation"

class ConversationResponse(BaseModel):
    user_id: str
    response: str

# making the chains dictionary
chains: dict[str, ConversationChain] = {}

shared_memories = {}

def get_or_create_shared_memory(user_id: str, k: int = 4):
    """Get or create a shared memory instance for a user"""
    if user_id not in shared_memories:
        shared_memories[user_id] = ConversationBufferWindowMemory(
            k=k, 
            return_messages=True, 
            memory_key="chat_history"
        )
    return shared_memories[user_id]

def get_conversation_chain(user_id: str, agent_type: str = "general", k: int = 4) -> ConversationChain:
    """Get or create a conversation chain for a user and agent type."""
    if user_id not in chains:
        chains[user_id] = {}
    
    if agent_type not in chains[user_id]:
        # Configure the language model based on agent type
        if agent_type == "documentation":
            temperature = 0.0
            max_tokens = 100
        elif agent_type == "diagram":
            temperature = 0.0
            max_tokens = 100
        elif agent_type == "code":
            temperature = 0.0
            max_tokens = 100
        else:  # general conversation
            temperature = 0.2
            max_tokens = 100
        
        # Create LangChain LLM wrapper
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=temperature,
            top_p=0.95,
            top_k=40,
            max_output_tokens=max_tokens,
            google_api_key=api_key,
        )
        
        # Create memory for this conversation chain
        memory = ConversationBufferWindowMemory(k=k, return_messages=True, memory_key="chat_history")
        
        # Create and store the chain
        chains[user_id][agent_type] = ConversationChain(llm=llm, memory=memory, verbose=False)
    
    return chains[user_id][agent_type]

# First chain: 
def create_documentation_chain(user_id: str) -> LLMChain:
    """Create a specialized chain for generating Jira stories."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.4,
        top_p=0.95,
        top_k=40,
        max_output_tokens=300,
        google_api_key=api_key,
    )
    
    jira_template = """Generate Jira user stories for the following software requirement:
    
    "{requirement}"
    
    For each user story:
    1. Create a clear title in the format "As a [user type], I want to [action] so that [benefit]"
    2. Add a detailed description
    3. Add acceptance criteria (at least 3 per story)
    4. Assign story points (1, 2, 3, 5, 8, 13)
    5. Set priority (Highest, High, Medium, Low, Lowest)
    
    Create at least 5 user stories that cover the main functionality.
    Format the output in Markdown with each story as a separate section.
    
    Chat History:
    {chat_history}
    """
    
    prompt = PromptTemplate(
        input_variables=["requirement", "chat_history"],
        template=jira_template
    )
    
    memory = get_or_create_shared_memory(user_id)
    return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

# Second chain: Modify jira
def create_jira_modification_chain(user_id: str) -> LLMChain:
    """Create a specialized chain for modifying existing Jira stories based on new requirements."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0,
        top_p=0.95,
        top_k=40,
        max_output_tokens=300,
        google_api_key=api_key,
    )
    
    # Modified template with a single input variable
    modification_template = """You are reviewing and modifying a set of Jira user stories based on additional requirements or feedback.

{input}

Please modify the existing Jira stories to incorporate these additional requirements. You can:
1. Update existing story titles, descriptions, or acceptance criteria
2. Add new acceptance criteria to existing stories
3. Add entirely new stories if needed
4. Adjust story points or priorities if appropriate

Maintain the same format as the original stories:
- Clear title in the format "As a [user type], I want to [action] so that [benefit]"
- Detailed description
- Acceptance criteria (at least 3 per story)
- Story points (1, 2, 3, 5, 8, 13)
- Priority (Highest, High, Medium, Low, Lowest)

Format the output in Markdown with each story as a separate section.
Highlight the changes you've made by placing [MODIFIED] or [NEW] tags next to modified or new elements.

Chat History:
{chat_history}
"""
    
    # Updated prompt with a single input variable
    prompt = PromptTemplate(
        input_variables=["input", "chat_history"],
        template=modification_template
    )
    
    # Create memory for this conversation chain
    memory = get_or_create_shared_memory(user_id)
    
    # Create and return the chain
    return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

# Request handlers
@app.get("/")
def read_root():
    return {"status": "ok", "message": "API running correctly with LangChain integration"}

## Documentation generation endpoint
@app.post("/generate/jira-stories")
async def generate_jira_stories(request: DocumentationRequest):
    """Generate Jira user stories using the documentation agent."""
    try:
        if not request.user_id:
            request.user_id = str(uuid4())
            
        # Create or get documentation chain (now used for Jira stories)
        jira_chain = create_documentation_chain(request.user_id)


        shared_memory = get_or_create_shared_memory(request.user_id)
        shared_memory.save_context(
            {"input": f"Requirement: {request.requirement}"}, 
            {"output": "I'll generate Jira stories for this requirement."}
        )
        
        # Generate Jira stories
        jira_stories = jira_chain.predict(
            requirement=request.requirement,
            chat_history=shared_memory.load_memory_variables({})["chat_history"])
        
        shared_memory.save_context(
            {"input": "Please generate Jira stories"}, 
            {"output": jira_stories}
        )
        # Clean the output if needed
        jira_stories = jira_stories.strip()
        
        return {
            "user_id": request.user_id,
            "jira_stories": jira_stories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Jira stories generation error: {str(e)}")


## Changing the documentation endpoint
@app.post("/modify_jira_stories/", response_model=ConversationResponse)
async def modify_jira_stories(request: ModifyJiraStoriesRequest):
    user_id = request.user_id or str(uuid4())
    
    # Use the agent_type from the request (defaults to "documentation")
    agent_type = request.agent_type
    
    # Get the modification chain
    modification_chain = create_jira_modification_chain(user_id)
    
    # If original stories aren't provided, try to find them in memory
    original_stories = request.original_stories
    if not original_stories and user_id in shared_memories:
        # Extract the last assistant message that might contain Jira stories
        memory = shared_memories[user_id]
        memory_messages = memory.chat_memory.messages
        
        for msg in reversed(memory_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                original_stories = msg.content
                break
    
    # If we still don't have original stories, return an error
    if not original_stories:
        raise HTTPException(
            status_code=400, 
            detail="No original stories provided or found in conversation history"
        )
    
    # Combine the inputs into a single input string
    combined_input = f"""Original Jira Stories:
{original_stories}

Additional Requirements/Feedback:
"{request.modification_prompt}"
"""
    
    # Add the interaction to shared memory
    shared_memory = get_or_create_shared_memory(user_id)
    shared_memory.save_context(
        {"input": f"Request to modify Jira stories: {request.modification_prompt}"}, 
        {"output": "Processing modification request..."}
    )
    
    # Run the chain with the single combined input
    response = modification_chain.run(input=combined_input)
    
    # Save the modified stories to memory
    shared_memory.save_context(
        {"input": "Please update the Jira stories"}, 
        {"output": response}
    )
    
    return ConversationResponse(user_id=user_id, response=response)