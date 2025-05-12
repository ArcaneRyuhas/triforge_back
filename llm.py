# API 
# pip install fastapi uvicorn python-dotenv google-generativeai

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# LLM
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load the environment
load_dotenv()

# Set the environment variable
api_key = os.getenv("GENAI_API_KEY")
if not api_key:
    raise ValueError("No se encontró la API_KEY. Asegúrate de tener un archivo .env con GENAI_API_KEY definida")

genai.configure(api_key=api_key)

## Set up the API 
app = FastAPI(title="Generative AI API", description="API para generar activos de proyecto con Google Generative AI")

## Connect to REACT
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
    return {"status": "ok", "message": "API funcionando correctamente"}

def generate_project_assets(requirement: str, format: str, language: str):
    try:
        # Construir el prompt
        prompt = f"""
        Based on the following software requirement: "{requirement}", generate:
        1. A clear and detailed project documentation (overview, features, tech stack, and milestones)
        2. A design diagram in "{format}" format
        3. An executable code scaffold in the following "{language}" language

        Format the output as a JSON with keys: documentation, diagram, code.
        """

        # Configuración del modelo
        generation_config = {
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 4096,
        }

        # Crear instancia del modelo (usando el modelo correcto de Gemini)
        model = genai.GenerativeModel(
            model_name="gemini-pro",  # Modelo correcto de Gemini
            generation_config=generation_config
        )

        # Hacer la solicitud al modelo
        response = model.generate_content(prompt)
        
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
    """
    Genera documentación, diagrama y código base a partir de un requerimiento.
    
    Parameters:
    - requirement: Descripción del requerimiento del software
    - format: Formato para el diagrama (ej. "Mermaid.js")
    - language: Lenguaje de programación para el código (ej. "Python")
    
    Returns:
    - JSON con documentación, diagrama y código
    """
    try:
        result = generate_project_assets(req.requirement, req.format, req.language)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# uvicorn prueba:app --reload