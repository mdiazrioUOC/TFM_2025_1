import json
from pydantic import BaseModel
from langchain_core.runnables import chain
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

llm = init_chat_model("o4-mini", model_provider="openai")


system = """Eres una herramienta que sirve para extraer fenotipos de la ontología Human Phenotype Ontolgy a partir de notas clínicas para ello: 
1. A partir del siguiente texto clínico, identifica todos los fenotipos clínicos relevantes, incluyendo diagnósticos, síntomas, signos físicos y hallazgos de laboratorio. 
2. Ignora por completo los hallazgos negativos, los hallazgos normales (es decir, «normal» o «no»), los procedimientos y los antecedentes familiares. 
3. Si algún valor incluye de forma implícita un fenotipo, infiérelo y menciónalo como tal.
4. Para cada término, asigna el código HPO apropiado. 
Devuelve un JSON con dos llaves: "final answer" con un listado de códigos HPO detectado y "descripciones" con un listado de los nombres de los fenotipos detectados.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{clinical_note}"),
    ]
)

init_chain = prompt | llm

@chain
def rawgptchain(question):
    response = init_chain.invoke(question)
    return json.loads(response.content)