import pickle as pkl
from rapidfuzz import process, fuzz
from rapidfuzz.utils import default_process

with open("../../resources/fuzzy_retriever.pkl", 'rb') as fp:
    data = pkl.load(fp)

class FuzzyRetriever:
    search_entries = data["search_entries"]
    ids_list = data["ids"]

    def invoke(self, query):
        results = process.extract(query, self.search_entries, scorer=fuzz.QRatio, processor=default_process, score_cutoff=80)
        return [(self.ids_list[result[2]], result[0], result[1]) for result in results]
