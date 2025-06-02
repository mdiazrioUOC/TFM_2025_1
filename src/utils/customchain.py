import os
import re
import json
import chromadb
import pandas as pd
import pickle as pkl
from typing import Optional
from dotenv import load_dotenv
from langsmith import traceable
from typing import List, Optional
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.runnables import chain
from langchain.chat_models import ChatOpenAI
from utils.fuzzyretriever import FuzzyRetriever
from langchain_voyageai import VoyageAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

def process_unique_metadata(doc_array, ontology, MAX_DOCS=5):
    unique_ids = []
    i=0
    while len(unique_ids) < MAX_DOCS and i<len(doc_array):
        if doc_array[i].metadata["hpo_id"] not in unique_ids:
            unique_ids.append(doc_array[i].metadata["hpo_id"] )
        i += 1
    return ontology.get_by_ids(unique_ids)

PROJECT_DIR = os.environ["PROJECT_DIR"]

llm = init_chat_model("o4-mini", model_provider="openai")
# llm = ChatOllama(model="llama3.1:8b")
# llm = ChatOllama(model="qwen3:8b")


embeddings_model = VoyageAIEmbeddings(model="voyage-3")

system =  """Eres un experto de codificación de fenotipos de la ontología Human Phenotype Ontology. Para ello primero debes determinar qué fenotipos están presentes en la nota clínica. Sigue los siguientes pasos: 
1. A partir del siguiente texto clínico, identifica términos del texto que sugieran fenotipos clínicos relevantes, incluyendo diagnósticos, síntomas, signos físicos, hallazgos de laboratorio y modos de herencia.  
2. Si algún valor incluye de forma implícita un fenotipo, infiérelo y menciónalo como tal en el campo "phenotype".
3. Si el valor no permite inferir con seguridad un fenotipo, simplemente describe el resultado de la analítica en lenguaje natural.
4. Para cada término (extract), a parte del fenotipo, incluye la frase a la que pertenezca en la nota clínica original (context).
5. Sé específico, cada término debe contener un solo fenotipo asociado. Si tiene dos fenotipos, duplícalo y menciona ambos fenotipos. 
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{clinical_note}"),
    ]
)

chroma_client = chromadb.HttpClient(host=os.environ['CHROMADB_CONNECTION'], port=8001)
vectordb = Chroma(client=chroma_client, embedding_function=embeddings_model, 
                  collection_name="hpo_ontology_esp_FULL")
retriever = vectordb.as_retriever(search_kwargs={"k": 7})
fuzzyretriever = FuzzyRetriever()

with open(os.path.join(PROJECT_DIR, "resources", "keyword_retriever.pkl"), "rb") as fp:
    keyword_retriever = pkl.load(fp)

ensemble_retriever = EnsembleRetriever(retrievers=[retriever,
                                                   keyword_retriever],
                                       weights=[0.6, 0.4], id_key="hpo_id")

class PhenotypeCandidate(BaseModel):
    """Fenotipos, patrones de herencia genética, anomalías anatómicas, síntomas clínicos, hallazgos diagnósticos, resultados de pruebas y afecciones o síndromes específicos en la nota clínica"""
    extract: str = Field(description="Un único fenotipo, diagnóstico, sintoma clínico, anomalia anatómica o prueba de laboratorio")
    phenotype: str = Field(description="Nombre del posible fenotipo asociado en español")
    context: str = Field( description="Parte de la frase en el que se menciona el extracto.")


class Data(BaseModel):
    """Información extraída sobre los fenotipos encontrados y los términos y contexto en el que se encuentran"""
    candidates: List[PhenotypeCandidate]

structured_llm = llm.with_structured_output(schema=Data)

extractphenotypes = prompt | structured_llm


sys_template = """Identifica el término de la Ontología de Fenotipos Humanos (HPO) más apropiado para cada extracto de las notas clínicas del paciente a partir de una lista de candidatos (Código HPO - Descripción).
Da prioridad a los términos que sean concisos y directamente pertinentes para el síntoma o afección principal descritos. 
Céntrate en el tema central de cada frase y evita seleccionar opciones con detalles descriptivos o situacionales adicionales a menos que sean esenciales para captar con precisión el fenotipo. 
Asegúrate de que el término HPO elegido coincide exactamente con la afección del paciente tal como se describe, sin añadir términos nuevos o extraños. Si crees que no encaja mínimamente, no selecciones ningún candidato.
Si hay varios candidatos, selecciona y devuelve el término HPO más pertinente que mejor represente la afección o síntoma primario. Si ves que ningún código encaja, deja el campo a nulo. La nota clínica original es la siguiente:
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
        default=None, description="Código HPO detectado con el formato HP:#######."
    )

llm_output = llm.with_structured_output(HpoCode)
hpo_assignment = chat_template | llm_output

def pretty_print_candidates(docs):
    final_str = ""
    for doc in docs: 
        final_str += f"{doc.id} - {doc.page_content}\n"
    return final_str

def encontrar_indices(cadena_larga, cadena_corta):
    inicio = cadena_larga.find(cadena_corta)
    if inicio == -1:
        return None  
    fin = inicio + len(cadena_corta)
    return inicio, fin

@chain
def custom_chain(question, with_positions=False):
    response = extractphenotypes.invoke(question)
    docs = []
    idxs = []
    intermediate_results = []
    for query in response.candidates:
        new_docs = retriever.invoke(query.extract)
        new_docs_ids = [doc.id for doc in new_docs]
        fuzzy_docs = [x[0] for x in fuzzyretriever.invoke(query.phenotype)]
        fuzzy_docs = [doc for doc in fuzzy_docs if doc not in new_docs_ids]
        new_docs =  vectordb.get_by_ids(set(fuzzy_docs)) + new_docs if len(set(fuzzy_docs)) > 0 else new_docs
        docs.append({"clinical_note":question,
                     "term":query.extract,
                     "phenotype":query.phenotype,
                     "context":query.context,
                     "candidates":pretty_print_candidates(new_docs)})
        intermediate_results.append([doc.id for doc in new_docs])  
        if with_positions:
            idxs.append(encontrar_indices(question['clinical_note'], query.extract))
    answer = hpo_assignment.batch(docs)
    answer = {"final_answer": answer, "docs": intermediate_results}
    if with_positions:
        answer["positions"] = idxs
    return answer