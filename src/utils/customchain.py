import os
import re
import json
import chromadb
import pandas as pd
import pickle as pkl
from utils.utils import *
from dotenv import load_dotenv
from langsmith import traceable
from models.HpoCode import HpoCode
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.runnables import chain
from langchain.chat_models import ChatOpenAI
from utils.fuzzyretriever import FuzzyRetriever
from langchain_voyageai import VoyageAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain.retrievers import EnsembleRetriever
from models.PhenotypeCandidates import PhenotypeData
from langchain_core.prompts import ChatPromptTemplate
from utils.prompts import first_call_prompt, second_call_prompt


PROJECT_DIR = os.environ["PROJECT_DIR"]

#Init models
llm = init_chat_model("o4-mini", model_provider="openai")
# llm = ChatOllama(model="llama3.1:8b")
# llm = ChatOllama(model="qwen3:8b")
embeddings_model = VoyageAIEmbeddings(model="voyage-3")


#Init retrievers
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


#first call settings
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", first_call_prompt),
        ("human", "{clinical_note}"),
    ]
)
structured_llm = llm.with_structured_output(schema=PhenotypeData)
extractphenotypes = prompt | structured_llm


#second call settings
human_template =  """Término: {term} ({phenotype})
Contexto: {context}
Candidatos: {candidates}"""

chat_template = ChatPromptTemplate.from_messages([
    ('system', second_call_prompt),
    ('human', human_template)
])
llm_output = llm.with_structured_output(HpoCode)
hpo_assignment = chat_template | llm_output


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