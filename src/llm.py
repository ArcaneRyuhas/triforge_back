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

class DiagramGenerationRequest(BaseModel):
    diagram_format: str = "Mermaid.js"
    user_id: Optional[str] = None
    diagram_type: Optional[str] = None
    jira_stories: Optional[str] = None
    agent_type: Optional[str] = "diagram"

class ModifyDiagramRequest(BaseModel):
    user_id: str
    modification_prompt: str
    original_diagram_code: Optional[str] = None
    agent_type: Optional[str] = "diagram"

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
            max_tokens = 300
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
        max_output_tokens=400,
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
        temperature=0.1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=400,
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
5. Do not add any nodes or edges unless explicitly requested
6. Do not refactor existing flows unless instructed

Maintain the same format as the original stories:
- Clear title in the format "As a [user type], I want to [action] so that [benefit]"
- Detailed description
- Acceptance criteria (at least 3 per story)
- Story points (1, 2, 3, 5, 8, 13)
- Priority (Highest, High, Medium, Low, Lowest)

Format the output in Markdown with each story as a separate section. Please ensure that you strictly adhere to only the changes outlined in the 'Modification Request' and make no other changes.
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

# Third Chain: Diagram Generation
def create_diagram_generation_chain(user_id: str) -> LLMChain:
    """Create a specialized chain for generating diagrams based on Jira stories."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0,  
        top_p=0.95,
        top_k=40,
        max_output_tokens=300,  
        google_api_key=api_key,
    )
    
    # Template for diagram generation
    diagram_template = """You are a software architect who creates diagrams based on Jira user stories.

{input}

Please create a diagram that represents the system described in these Jira stories.

The output should be in Mermaid.js format:
- Use appropriate Mermaid syntax based on the diagram type
- Include all key entities, actors, and their relationships
- Use clear labels and descriptive text
- Include all important user flows mentioned in the requirements
- Make sure the diagram is valid Mermaid.js syntax

IMPORTANT: Return ONLY the Mermaid.js code without any explanations, preamble, or ```mermaid tags. Do not wrap the code in markdown code blocks. The response should start directly with the Mermaid syntax (like "graph TD" or "sequenceDiagram").

Reference for diagram types and their Mermaid.js syntax:
- flowchart: graph TD or graph LR
- sequence: sequenceDiagram
- class: classDiagram
- entity-relationship: erDiagram
- state: stateDiagram-v2
- gantt: ganttChart
- user journey: journey

Chat History:
{chat_history}
"""
    
    # Prompt with only input and chat_history variables (removed diagram_type)
    prompt = PromptTemplate(
        input_variables=["input", "chat_history"],
        template=diagram_template
    )
    
    # Use the shared memory for this user
    memory = get_or_create_shared_memory(user_id)
    
    # Create and return the chain
    return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

# Fourth Chain: Modify Diagram
def create_diagram_modification_chain(user_id: str) -> LLMChain:
    """Create a specialized chain for modifying existing Mermaid.js diagrams."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0, # Low temperature for precise modifications
        top_p=0.95,
        top_k=40,
        max_output_tokens=300,
        google_api_key=api_key,
    )
    
    # Template for diagram modification
    modification_template = """You are a software architect who modifies existing Mermaid.js diagrams.

{input}

Please modify the provided Mermaid.js diagram based *strictly* on the "Modification Request".
Ensure the modified diagram remains valid Mermaid.js syntax.
Maintain the diagram type (e.g., flowchart, sequence) of the original diagram unless explicitly told to change it.

**CRITICAL INSTRUCTION:**
- **ONLY** make the changes explicitly described in the "Modification Request".
- **DO NOT** add any new nodes, edges, or alter any existing parts of the diagram *unless specifically commanded to by the "Modification Request"*.
- **DO NOT** refactor, simplify, or improve existing flows or elements that are not directly targeted by the "Modification Request".
- The output should be the **complete, valid Mermaid.js code for the entire diagram**.
- **DO NOT** include any explanations, preamble, or markdown code block tags (```mermaid or ```).

Chat History:
{chat_history}
"""
    
    prompt = PromptTemplate(
        input_variables=["input", "chat_history"],
        template=modification_template
    )
    
    memory = get_or_create_shared_memory(user_id)
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

## Diagram generation endpoint
@app.post("/generate/diagram", response_model=ConversationResponse)
async def generate_diagram(request: DiagramGenerationRequest):
    """Generate a diagram based on Jira stories and diagram type."""
    user_id = request.user_id or str(uuid4())

    # Get the diagram generation chain
    diagram_chain = create_diagram_generation_chain(user_id)

    # If Jira stories aren't provided, try to find them in memory
    jira_stories = request.jira_stories
    if not jira_stories and user_id in shared_memories:
        memory = shared_memories[user_id]
        memory_messages = memory.chat_memory.messages

        # Iterate through messages in reverse to find the last AI response that looks like Jira stories
        for msg in reversed(memory_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                # A simple heuristic: check for Markdown headers that might indicate Jira stories
                # This could be refined based on the exact output format of generate_jira_stories
                if re.search(r"##\s*As a\s*", msg.content) or "story points" in msg.content.lower():
                    jira_stories = msg.content
                    break

    # If we still don't have Jira stories, return an error
    if not jira_stories:
        raise HTTPException(
            status_code=400,
            detail="No Jira stories provided or found in conversation history. Please generate stories first or provide them."
        )

    # Validate diagram type
    diagram_type = request.diagram_type
    if not diagram_type:
        raise HTTPException(
            status_code=400,
            detail="Diagram type (e.g., 'flowchart', 'sequence', 'class') is required."
        )
    
    # Map common terms to Mermaid diagram types
    diagram_type_mapping = {
        "flow": "flowchart",
        "flowchart": "flowchart",
        "sequence": "sequence", 
        "class": "class",
        "er": "entity-relationship",
        "entity relationship": "entity-relationship",
        "state": "state",
        "gantt": "gantt",
        "user journey": "user journey",
        "journey": "user journey"
    }
    
    # Normalize diagram type
    normalized_diagram_type = diagram_type.lower()
    if normalized_diagram_type in diagram_type_mapping:
        normalized_diagram_type = diagram_type_mapping[normalized_diagram_type]
    
    # Combine the inputs into a single input string including the diagram type
    combined_input = f"""Jira User Stories:
{jira_stories}

Diagram Type: {normalized_diagram_type}
"""
    
    # Add the interaction to shared memory
    shared_memory = get_or_create_shared_memory(user_id)
    shared_memory.save_context(
        {"input": f"Generate a {normalized_diagram_type} diagram for these Jira stories"}, 
        {"output": "Processing diagram generation request..."}
    )
    
    # Run the chain with only the combined input (no diagram_type parameter)
    response = diagram_chain.run(input=combined_input)
    
    # Clean the output to ensure we get only the Mermaid code
    clean_response = response.strip()
    
    # Remove markdown code block syntax if present
    if clean_response.startswith("```mermaid"):
        clean_response = clean_response[len("```mermaid"):].strip()
    if clean_response.startswith("```"):
        clean_response = clean_response[3:].strip()
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3].strip()
        
    # Remove common prefixes the model might add
    prefixes_to_remove = [
        "Here's a Mermaid.js diagram:",
        "Here is the Mermaid.js diagram:",
        "Here's the diagram:",
        "Mermaid.js code:",
        "Diagram:"
    ]
    
    for prefix in prefixes_to_remove:
        if clean_response.startswith(prefix):
            clean_response = clean_response[len(prefix):].strip()
    
    # Save the generated diagram to memory
    shared_memory.save_context(
        {"input": f"Generate a {normalized_diagram_type} diagram"}, 
        {"output": clean_response}
    )
    
    return ConversationResponse(user_id=user_id, response=clean_response)

## Diagram modification endpoint
@app.post("/modify_diagram", response_model=ConversationResponse)
async def modify_diagram(request: ModifyDiagramRequest):
    """Modify an existing Mermaid.js diagram based on a modification prompt."""
    user_id = request.user_id or str(uuid4())
    
    # Get the diagram modification chain
    modification_chain = create_diagram_modification_chain(user_id)
    
    # If original_diagram_code isn't provided, try to find it in memory
    original_diagram_code = request.original_diagram_code
    if not original_diagram_code and user_id in shared_memories:
        memory = shared_memories[user_id]
        memory_messages = memory.chat_memory.messages
        
        for msg in reversed(memory_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                # Heuristic to identify Mermaid.js diagrams from previous AI output
                # Check for common Mermaid.js starting keywords
                if msg.content.strip().startswith(("graph", "sequenceDiagram", "classDiagram", "erDiagram", "stateDiagram", "gantt", "journey")):
                    original_diagram_code = msg.content
                    break
    
    # If we still don't have original diagram code, return an error
    if not original_diagram_code:
        raise HTTPException(
            status_code=400, 
            detail="No original diagram code provided or found in conversation history. Please generate a diagram first or provide the code."
        )
    
    # Combine the inputs into a single input string for the LLM
    combined_input = f"""Existing Mermaid.js Diagram:
{original_diagram_code}

Modification Request:
"{request.modification_prompt}"
"""
    
    # Add the interaction to shared memory
    shared_memory = get_or_create_shared_memory(user_id)
    shared_memory.save_context(
        {"input": f"Request to modify diagram: {request.modification_prompt}"}, 
        {"output": "Processing diagram modification request..."}
    )
    
    # Run the chain with the single combined input
    response = modification_chain.run(input=combined_input)
    
    # Clean the output to ensure we get only the Mermaid code
    clean_response = response.strip()
    
    # Remove markdown code block syntax if present
    if clean_response.startswith("```mermaid"):
        clean_response = clean_response[len("```mermaid"):].strip()
    if clean_response.startswith("```"):
        clean_response = clean_response[3:].strip()
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3].strip()
        
    # Remove common prefixes the model might add
    prefixes_to_remove = [
        "Here's the modified Mermaid.js diagram:",
        "Here is the modified Mermaid.js diagram:",
        "Modified Diagram:",
        "Mermaid.js code:",
        "Diagram:"
    ]
    
    for prefix in prefixes_to_remove:
        if clean_response.startswith(prefix):
            clean_response = clean_response[len(prefix):].strip()
            
    # Save the modified diagram to memory
    shared_memory.save_context(
        {"input": "Please update the diagram"}, 
        {"output": clean_response}
    )
    
    return ConversationResponse(user_id=user_id, response=clean_response)