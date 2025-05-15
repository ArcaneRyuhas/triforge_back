from pydantic import BaseModel

class Parsingstructure(BaseModel):
    documentation: str
    diagrams: str
    code: str
