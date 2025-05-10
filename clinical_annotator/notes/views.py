import os
import json
import dotenv
import requests
import pandas as pd
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

dotenv.load_dotenv()
URL = os.environ["PROCESS_API_URL"]

class HPOCode:
    def __init__(self, code, name, start=None, end=None, candidates=[]):
        self.code = code
        self.name = name
        self.start = start
        self.end = end
        self.candidates = candidates
    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "candidates": [candidate.to_dict() if isinstance(candidate, HPOCode) else candidate for candidate in self.candidates],
        }
    @classmethod
    def from_dict(cls, data):
        return [cls(
            code=item["code"],
            name=item["name"],
            start=item["start"],
            end=item["end"],
            candidates=item["candidates"]) for item in data]

def load_hpo_codes():
    """Load HPO codes from a CSV file and return them as a list of dictionaries."""
    csv_path = os.path.join(settings.STATICFILES_DIRS[0],'HPO_ontology.csv')
    hpo_df = pd.read_csv(csv_path)
    hpo_df.columns=["index", "hpo_code", "hpo_name"]
    hpo_dict = dict(zip(hpo_df["hpo_code"], hpo_df["hpo_name"]))
    return hpo_dict


def extract_hpo_codes(request):
    """Extract HPO codes from the clinical note using an external API."""
    if "hpo_ontology" not in request.session:
        request.session["hpo_ontology"] = load_hpo_codes()
    data = {'clinical_note': request.session['clinical_note']}
    response = requests.post(URL, json=data)
    if response.status_code != 200:
        request.session['hpo_codes'] = []
    else:
        data = eval(response.json()['result'])
        hpo_objects = []
        for i, answer in enumerate(data["final_answer"]):
            code = answer["hpo_code"]
            start, end = data["positions"][i]
            candidates = [HPOCode(code=hpo_code, name=request.session["hpo_ontology"][hpo_code]) for hpo_code in data["docs"][i]]
            obj = HPOCode(code=code, name=request.session["hpo_ontology"][code], start=start, end=end, candidates=candidates)
            hpo_objects.append(obj)
        
        request.session['hpo_codes'] = [hpo_code.to_dict() for hpo_code in hpo_objects]
    return 

def clinical_note_processed(request):
    """Validation view for the clinical note."""
    clinical_note = request.session['clinical_note']
    hpo_codes = HPOCode.from_dict(request.session['hpo_codes'])
    return render(request, "notes/clinical_note_processed.html", {
        "clinical_note": clinical_note,
        "hpo_codes": hpo_codes,
        'range': range(len(clinical_note))
    })

def add_clinical_note(request):
    """View to add a clinical note."""
    note = ""
    result=""
    if request.method == "POST":
        clinical_note = request.POST.get("clinical_note", "")
        request.session['clinical_note'] = clinical_note
        extract_hpo_codes(request)
        return redirect('clinical_note_processed')  # Replace with your URL name
    return render(request, "notes/add_clinical_note.html", {"note": note, "result":result})

@csrf_exempt
def delete_hpo_code(request):
    """Delete an HPO code from the session."""
    if request.method == "POST":
        data = json.loads(request.body)
        code_to_delete = data.get("code")
        request.session['hpo_codes'] = [code for code in request.session['hpo_codes'] if code["code"] != code_to_delete]
        print(request.session['hpo_codes'])
        return JsonResponse({"status": "deleted"})

def add_hpo_code(request):
    """Add a new HPO code to the session."""
    if request.method == "POST":
        hpo_code = request.POST.get('hpo_code').split('-')
        new_hpo_code = HPOCode(hpo_code[0], hpo_code[1], 
                               request.POST.get('start_position'), 
                               request.POST.get('end_position'), [])
        request.session['hpo_codes'] = request.session['hpo_codes'] + [new_hpo_code.to_dict()]
        return redirect('clinical_note_processed')

@csrf_exempt
def exchange_hpo_code(request):
    """Exchange an HPO code in the session."""
    if request.method == "POST":
        data = json.loads(request.body)
        hpo_code = data.get("code")
        hpo_name = data.get("name")
        counter = data.get('counter') - 1
        hpo_codes = request.session['hpo_codes']
        hpo_to_change = hpo_codes.pop(counter)
        new_candidates = [candidate for candidate in hpo_to_change["candidates"] if candidate["code"] != hpo_code]
        new_code = HPOCode(hpo_code, hpo_name, hpo_to_change["start"], hpo_to_change["end"], [hpo_to_change] + new_candidates)
        hpo_codes.insert(counter, new_code.to_dict())
        request.session['hpo_codes'] = hpo_codes
        return redirect('clinical_note_processed')

@require_GET
def search_hpo_terms(request):
    """Search for HPO terms based on the query parameter for the dropdown."""
    ontology = request.session['hpo_ontology']
    term = request.GET.get("q", "").lower()
    selected_codes = [{'hpo_code':code, 'hpo_name':name} for code,name in ontology.items() if term in name.lower()]
    return JsonResponse({'results': selected_codes})