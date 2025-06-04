from typing import List, Optional
from pydantic import BaseModel, Field

class PhenotypeCandidate(BaseModel):
    """Fenotipos, patrones de herencia genética, anomalías anatómicas, síntomas clínicos, hallazgos diagnósticos, resultados de pruebas y afecciones o síndromes específicos en la nota clínica"""
    extract: str = Field(description="Un único fenotipo, diagnóstico, sintoma clínico, anomalia anatómica o prueba de laboratorio")
    phenotype: str = Field(description="Nombre del posible fenotipo asociado en español")
    context: str = Field( description="Parte de la frase en el que se menciona el extracto.")


class PhenotypeData(BaseModel):
    """Información extraída sobre los fenotipos encontrados y los términos y contexto en el que se encuentran"""
    candidates: List[PhenotypeCandidate]