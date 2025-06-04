# Clinical Annotator – Django Application

This Django application offers a web-based tool for clinical text annotation, enabling users to input, process, edit, and validate phenotype annotations based on the Human Phenotype Ontology (HPO).

## Getting Started

### Prerequisites

- Python 3.8+
- Docker (optional but recommended)
- `pip` or `pipenv` for dependency management

### Installation

1. **Clone the repository**:

```bash
git clone https://github.com/mdiazrioUOC/TFM_2025_1.git
cd TFM_2025_1/clinical-annotator
```

2. **Create an .env file at this location and add the following variable:**

```bash
PROCESS_API_URL=http://your-api-url/api/annotate/
```

Replace http://your-api-url/api/annotate/ with the actual URL where the annotation API is hosted.

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run migrations**

```bash
python manage.py migrate
```

5. **Start development server**

```bash
python manage.py runserver
```

## Processing API

This application uses an external API to annotate input clinical text with HPO concepts.
This API should be able to:

1. Receive a POST request with a JSON payload

```json
{
  "text": "The patient shows signs of hepatomegaly and hypotonia."
}
```

2. Return a structed JSON object containing

- final_answer:a list of identified HPO codes.
- docs:ranked candidates per identified concept.
- positions:character positions in the original text where each HPO term was detected.

Example response:

```json
{
  "final_answer": [{ "hpo_code": "HP:0001945" }, { "hpo_code": "HP:0012378" }],
  "docs": [
    ["HP:0001945", "HP:0025215", "HP:0001954"],
    ["HP:0012378", "HP:0003388", "HP:0012431"]
  ],
  "positions": [
    [32, 38],
    [41, 47]
  ]
}
```

## Running with Docker

To run the app insde Docker:

```bash
docker build -t clinicalannotator:latest .
docker run --env-file .env -p 8000:8000 clinicalannotator:latest
```

## License

CC BY-NC License.
