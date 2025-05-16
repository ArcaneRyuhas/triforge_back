import os
import json
import tempfile
import re
import asyncio
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import google.generativeai as genai
from dotenv import load_dotenv


# API key part
load_dotenv()

api_key = os.getenv("GENAI_API_KEY")
if not api_key:
    raise ValueError("No API_KEY found. Ensure you have a .env file with GENAI_API_KEY defined")

# Gemini token
genai.configure(api_key=api_key)

# Initializing FastAPI and React
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test endpoint
@app.get("/")
def read_root():
    return {"status": "ok", "message": "API running correctly"}

# First Agent: documentation generation
async def documentation_agent(requirement):
    """Agent specialized in creating project documentation"""
    try:
        doc_config = {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 100,
        }
        
        model = genai.GenerativeModel("gemini-2.0-flash", generation_config=doc_config)
        
        prompt = f"""Generate comprehensive project documentation for the following software requirement:
        
        "{requirement}"
        
        Include:
        1. Project overview
        2. Key features (list at least 5-7 features)
        3. Technology stack recommendation
        4. Project milestones and estimated timeline
        5. Implementation challenges and considerations
        
        Format the documentation in Markdown format."""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Documentation generation error: {str(e)}"

# Second Agent: diagrams
async def diagram_agent(requirement, diagram_format):
    """Agent specialized in creating technical diagrams"""
    try:
        diagram_config = {
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 30,
            "max_output_tokens": 100,
        }
        
        model = genai.GenerativeModel("gemini-2.0-flash", generation_config=diagram_config)
        
        prompt = f"""Create a detailed {diagram_format} diagram that illustrates the architecture or key components for the following software requirement:
        
        "{requirement}"
        
        The diagram should:
        1. Show the main components of the system
        2. Illustrate the relationships between components
        3. Include any important data flows or processes
        4. Be detailed enough for implementation but not overly complex
        
        Provide ONLY the {diagram_format} code without any explanation or markdown formatting."""
        
        response = model.generate_content(prompt)
        diagram_text = response.text.strip()
        
        code_block_match = re.search(r"```(?:\w+)?\n(.*?)```", diagram_text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        return diagram_text
    except Exception as e:
        return f"Diagram generation error: {str(e)}"

#Third Agent: coding
async def code_agent(requirement, language):
    """Agent specialized in generating code scaffolds"""
    try:
        code_config = {
            "temperature": 0.0,  
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 100,
        }
        
        model = genai.GenerativeModel("gemini-2.0-flash", generation_config=code_config)
        
        prompt = f"""Generate a scaffolding code structure in {language} for the following software requirement:
        
        "{requirement}"
        
        The code should:
        1. Include all necessary imports and dependencies
        2. Implement core classes/functions with proper structure
        3. Include helpful comments explaining key components
        4. Follow best practices and design patterns for {language}
        5. Be executable or compilable without major modifications
        
        Provide ONLY the {language} code without any explanation or markdown formatting."""
        
        response = model.generate_content(prompt)
        code_text = response.text.strip()
        
        code_block_match = re.search(r"```(?:\w+)?\n(.*?)```", code_text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        return code_text
    except Exception as e:
        return f"Code generation error: {str(e)}"

#Output endpoint
@app.post("/generate/specialized")
async def generate_with_specialized_agents(
    requirement: str = Body(..., embed=True, description="Software requirement description"),
    format: str = Body(..., embed=True, description="Diagram format (e.g., 'Mermaid.js')"),
    language: str = Body(..., embed=True, description="Programming language (e.g., 'Python')")
):
    """Generate project assets using specialized agents for each component"""
    try:
        documentation, diagram, code = await asyncio.gather(
            documentation_agent(requirement),
            diagram_agent(requirement, format),
            code_agent(requirement, language)
        )
        
        output = {
            "documentation": documentation,
            "diagram": diagram,
            "code": code
        }
        
        return {
            "success": True,
            "output": output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in generation process: {str(e)}")