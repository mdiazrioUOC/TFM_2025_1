import os
import re
import json
import pandas as pd
import pickle as pkl
from dotenv import load_dotenv
from langsmith import traceable
from typing import List, Optional
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
from langchain_core.runnables import chain
from langchain.chat_models import ChatOpenAI
from langchain_voyageai import VoyageAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

llm = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
embeddings_model = VoyageAIEmbeddings(model="voyage-3")

system =  """Revisa cuidadosamente cada frase de la nota clínica para identificar términos relacionados con fenotipos, patrones de herencia genética, anomalías anatómicas, síntomas clínicos, hallazgos diagnósticos, resultados de pruebas y afecciones o síndromes específicos.
Ignora por completo los hallazgos negativos, los hallazgos normales (es decir, «normal» o «no»), los procedimientos y los antecedentes familiares. 
Asegúrate de que el resultado sea conciso, sin notas, comentarios ni metaexplicaciones adicionales. No dejes fuera adjetivos críticos para ese fenotipo.
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

with open("../../resources/keyword_retriever.pkl", "rb") as fp:
    keyword_retriever = pkl.load(fp)

ensemble_retriever = EnsembleRetriever(retrievers=[retriever,
                                                   keyword_retriever],
                                       weights=[0.6, 0.4], id_key="hpo_id")

class PhenotypeCandidate(BaseModel):
    """Información sobre los términos extraídos y su contexto. """
    extract: str = Field(default=None, description="Término extraído tal como aparece en el texto")
    context: str = Field(
        default=None, description="Frase entera en el que se menciona al término."
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
Si hay varios candidatos, selecciona y devuelve el término HPO más pertinente que mejor represente la afección o síntoma primario. Proporciona sólo los códigos HPO elegidos.
"""

human_template =  """Término: {term}
Contexto: {context}
Candidatos: {candidates}"""

chat_template = ChatPromptTemplate.from_messages([
    ('system', sys_template),
    ('human', human_template)
])

class HpoCode(BaseModel):
    """Código HPO asignado"""
    hpo_code: str

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
        docs.append({"term":query.extract,
                     "context":query.context,
                     "candidates":pretty_print_candidates(new_docs)})
        intermediate_results.append([doc.id for doc in new_docs])    
    answer = hpo_assignment.batch(docs)
    return {"final answer": answer, "docs": intermediate_results}