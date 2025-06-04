def process_unique_metadata(doc_array, ontology, MAX_DOCS=5):
    unique_ids = []
    i=0
    while len(unique_ids) < MAX_DOCS and i<len(doc_array):
        if doc_array[i].metadata["hpo_id"] not in unique_ids:
            unique_ids.append(doc_array[i].metadata["hpo_id"] )
        i += 1
    return ontology.get_by_ids(unique_ids)

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