first_call_prompt =  """Eres un experto de codificación de fenotipos de la ontología Human Phenotype Ontology. Para ello primero debes determinar qué fenotipos están presentes en la nota clínica. Sigue los siguientes pasos: 
1. A partir del siguiente texto clínico, identifica términos del texto que sugieran fenotipos clínicos relevantes, incluyendo diagnósticos, síntomas, signos físicos, hallazgos de laboratorio y modos de herencia.  
2. Si algún valor incluye de forma implícita un fenotipo, infiérelo y menciónalo como tal en el campo "phenotype".
3. Si el valor no permite inferir con seguridad un fenotipo, simplemente describe el resultado de la analítica en lenguaje natural.
4. Para cada término (extract), a parte del fenotipo, incluye la frase a la que pertenezca en la nota clínica original (context).
5. Sé específico, cada término debe contener un solo fenotipo asociado. Si tiene dos fenotipos, duplícalo y menciona ambos fenotipos. 
"""

second_call_prompt = """Identifica el término de la Ontología de Fenotipos Humanos (HPO) más apropiado para cada extracto de las notas clínicas del paciente a partir de una lista de candidatos (Código HPO - Descripción).
Da prioridad a los términos que sean concisos y directamente pertinentes para el síntoma o afección principal descritos. 
Céntrate en el tema central de cada frase y evita seleccionar opciones con detalles descriptivos o situacionales adicionales a menos que sean esenciales para captar con precisión el fenotipo. 
Asegúrate de que el término HPO elegido coincide exactamente con la afección del paciente tal como se describe, sin añadir términos nuevos o extraños. Si crees que no encaja mínimamente, no selecciones ningún candidato.
Si hay varios candidatos, selecciona y devuelve el término HPO más pertinente que mejor represente la afección o síntoma primario. Si ves que ningún código encaja, deja el campo a nulo. La nota clínica original es la siguiente:
{clinical_note}
"""