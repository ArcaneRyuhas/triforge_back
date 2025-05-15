# API 
# pip install fastapi uvicorn python-dotenv google-generativeai

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# LLM
from google import genai
from dotenv import load_dotenv
import os
from fastapi import Body

#archives
from models.parsingstructure import Parsingstructure

# Load the environment
load_dotenv()

# Set the environment variable
api_key = os.getenv("GENAI_API_KEY")
if not api_key:
    raise ValueError("No se encontró la API_KEY. Asegúrate de tener un archivo .env con GENAI_API_KEY definida")


## Set up the API 
app = FastAPI()

## Connect to REACT CHECAR
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequirementInput(BaseModel):
    requirement: str
    format: str  # For diagram (e.g. "Mermaid.js")
    language: str  # For code (e.g. "Python")


# Endpoint raíz para verificar que la API está funcionando
@app.get("/")
def read_root():
    return {"status": "ok", "message": "API working correctly"}


@app.post("/generate")
def generate_project_assets(
    requirement: str = Body(..., embed=True, description="Description of the software requirement"),
    format: str = Body(..., embed=True, description="Format for the diagram (e.g. 'Mermaid.js')"),
    language: str = Body(..., embed=True, description="Programming language for the code (e.g. 'Python')")
):
    client = genai.Client(api_key=api_key)

    try:
        #model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)
        prompt = f"""Generate a comprehensive software project asset package based on the following requirement: "{requirement}"
        Provide a detailed response with:
        1. Project Documentation
        - Clear project overview
        - Detailed feature list
        - Recommended technology stack
        - Project milestones and timeline

        2. Design Diagram
        - Create a diagram in "{format}" format
        - Should illustrate system architecture or key components

        3. Code Scaffold
        - Generate a basic code structure in "{language}"
        - Include key classes, functions, and project structure
        - Ensure the code is executable and follows best practices

        Format the entire output as a JSON with keys:
        - documentation: string (project documentation details)
        - diagram: string (diagram in specified format)
        - code: string (code scaffold in specified language)

        Ensure the response is comprehensive, clear, and directly applicable to the given requirement.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
            "response_mime_type": "application/json", 
            "max_output_tokens": 100, 
            "temperature": 0.1,
            "top_p": 1,
            "top_k": 1,
            "response_schema": list[Parsingstructure]
            }
        )

        output: list[Parsingstructure]=response.parsed

        return {
            "success": True,
            "output": output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error when generating the content {str(e)}")

"""

    


    #return {
        #"documentation": "Generación de documentación, diagrama y código base a partir de un requerimiento.",
        #"requirement": requirement,
        #"format": format,
        #"language": language
   # }





@app.post("/generate")
def generate_project_assets(
    requirement: str = Body(..., embed=True, description="Descripción del requerimiento del software"),
    format: str = Body(..., embed=True, description="Formato para el diagrama (ej. 'Mermaid.js')"),
    language: str = Body(..., embed=True, description="Lenguaje de programación para el código (ej. 'Python')")
):
    try: # Construir el prompt prompt = f
        Based on the following software requirement: "{requirement}", generate:
        1. A clear and detailed project documentation (overview, features, tech stack, and milestones)
        2. A design diagram in "{format}" format
        3. An executable code scaffold in the following "{language}" language

        Format the output as a JSON with keys: documentation, diagram, code.

        # Configuración del modelo
        generation_config = {
            "temperature": 0.1,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 1000,
        }

        # Crear instancia del modelo (usando el modelo correcto de Gemini)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config
        )

        # Hacer la solicitud al modelo
        response = model.generate_content(prompt)
        
        print('Tokens prompt', model.count_tokens(model="gemini-2.0-flash", contents=prompt))
        print('Tokens response', model.count_tokens(model="gemini-2.0-flash", contents=response))

        # Procesar la respuesta
        if hasattr(response, 'text'):
            try:
                # Intentar parsear la respuesta como JSON
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # Si no es JSON válido, devolver como texto
                return {
                    "documentation": "Error parsing JSON response",
                    "diagram": response.text,
                    "code": "Error in response format"
                }
        else:
            return {
                "error": "No se pudo generar una respuesta"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar contenido: {str(e)}")

@app.post("/requirement")
async def generate(req: RequirementInput):
    Genera documentación, diagrama y código base a partir de un requerimiento.
    
    Parameters:
    - requirement: Descripción del requerimiento del software
    - format: Formato para el diagrama (ej. "Mermaid.js")
    - language: Lenguaje de programación para el código (ej. "Python")
    
    Returns:
    - JSON con documentación, diagrama y código
    try:
        result = generate_project_assets(req.requirement, req.format, req.language)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# uvicorn prueba:app --reload
"""