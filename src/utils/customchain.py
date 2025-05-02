import os
import re
import json
import pandas as pd
import pickle as pkl
from typing import Optional
from dotenv import load_dotenv
from langsmith import traceable
from typing import List, Optional
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
from fuzzyretriever import FuzzyRetriever
from langchain_core.runnables import chain
from langchain.chat_models import ChatOpenAI
from langchain_voyageai import VoyageAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

llm = init_chat_model("o4-mini", model_provider="openai")
embeddings_model = VoyageAIEmbeddings(model="voyage-3")

system =  """Eres un experto de codificación de fenotipos de la ontología Human Phenotype Ontology. Para ello primero debes determinar qué fenotipos están presentes en la nota clínica. Sigue los siguientes pasos: 
1. A partir del siguiente texto clínico, identifica todos los fenotipos clínicos relevantes, incluyendo diagnósticos, síntomas, signos físicos y hallazgos de laboratorio. 
2. Ignora por completo los hallazgos negativos, los hallazgos normales (es decir, «normal» o «no»), los procedimientos y los antecedentes familiares. 
3. Si algún valor incluye de forma implícita un fenotipo, infiérelo y menciónalo como tal.
4. Si el valor no permite inferir con seguridad un fenotipo, simplemente describe el resultado de la analítica en lenguaje natural.
5. Sé específico, cada término debe contener un solo fenotipo asociado. Si tiene dos fenotipos, duplícalo y menciona ambos fenotipos. 
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{clinical_note}"),
    ]
)

vectordb = Chroma(persist_directory="../../chroma_db/Voyage3", embedding_function=embeddings_model, 
                  collection_name="hpo_ontology_esp_FULL")
retriever = vectordb.as_retriever(search_kwargs={"k": 3})
fuzzyretriever = FuzzyRetriever()

with open("../../resources/keyword_retriever.pkl", "rb") as fp:
    keyword_retriever = pkl.load(fp)

ensemble_retriever = EnsembleRetriever(retrievers=[retriever,
                                                   keyword_retriever],
                                       weights=[0.6, 0.4], id_key="hpo_id")

class PhenotypeCandidate(BaseModel):
    """Fenotipos, patrones de herencia genética, anomalías anatómicas, síntomas clínicos, hallazgos diagnósticos, resultados de pruebas y afecciones o síndromes específicos en la nota clínica"""
    extract: str = Field(default=None, description="Un único fenotipo, diagnóstico, sintoma clínico, anomalia anatómica o prueba de laboratorio")
    phenotype: str = Field(default=None, description="Nombre del posible fenotipo asociado en español")
    context: str = Field(
        default=None, description="Parte de la frase en el que se menciona el extracto."
    )


class Data(BaseModel):
    """Información extraída sobre los fenotipos encontrados"""
    candidates: List[PhenotypeCandidate]

structured_llm = llm.with_structured_output(schema=Data)

extractphenotypes = prompt | structured_llm


sys_template = """Identifica el término de la Ontología de Fenotipos Humanos (HPO) más apropiado para cada extracto de las notas clínicas del paciente a partir de una lista de candidatos (Código HPO - Descripción).
Da prioridad a los términos que sean concisos y directamente pertinentes para el síntoma o afección principal descritos. 
Céntrate en el tema central de cada frase y evita seleccionar opciones con detalles descriptivos o situacionales adicionales a menos que sean esenciales para captar con precisión el fenotipo. 
Asegúrate de que el término HPO elegido coincide estrechamente con la afección del paciente tal como se describe, sin añadir términos nuevos o extraños. 
Si hay varios candidatos, selecciona y devuelve el término HPO más pertinente que mejor represente la afección o síntoma primario. Proporciona sólo los códigos HPO elegidos. La nota clínica original es la siguiente:
{clinical_note}
"""

human_template =  """Término: {term} ({phenotype})
Contexto: {context}
Candidatos: {candidates}"""

chat_template = ChatPromptTemplate.from_messages([
    ('system', sys_template),
    ('human', human_template)
])

class HpoCode(BaseModel):
    """Código HPO asignado"""
    hpo_code: Optional[str] = Field(
        default=None, description="Código HPO detectado."
    )

llm_output = llm.with_structured_output(HpoCode)
hpo_assignment = chat_template | llm_output

def pretty_print_candidates(docs):
    final_str = ""
    for doc in docs: 
        final_str += f"{doc.id} - {doc.page_content}\n"
    return final_str

@chain
def custom_chain(question):
    response = extractphenotypes.invoke(question)
    docs = []
    intermediate_results = []
    for query in response.candidates:
        new_docs = ensemble_retriever.invoke(query.context)
        fuzzy_docs = [x[0] for x in fuzzyretriever.invoke(query.phenotype)]
        new_docs =  vectordb.get_by_ids(set(fuzzy_docs)) + new_docs if len(set(fuzzy_docs)) > 0 else new_docs
        docs.append({"clinical_note":question,
                     "term":query.extract,
                     "phenotype":query.phenotype,
                     "context":query.context,
                     "candidates":pretty_print_candidates(new_docs)})
        intermediate_results.append([doc.id for doc in new_docs])    
    answer = hpo_assignment.batch(docs)
    return {"final_answer": answer, "docs": intermediate_results}