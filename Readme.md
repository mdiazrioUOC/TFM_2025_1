This work has been carried out as part of the final thesis for the Master's degree in Bioinformatics and Biostatistics. The main focus of the project is the development of an application that enables automatic clinical note phenotype annotation, which is made accessible through an API. More detailed information about this Flask-based application can be found in this README file, and the core code is organized within the src folder. Additionally, a web interface has been created to facilitate requesting and validating these phenotype annotations. The code for this web interface, along with further details, is available in the clinical_annotator folder. In addition, the state of the GitHub repository at the time of each assessment has been saved as tags, including: [PEC2](https://github.com/mdiazrioUOC/TFM_2025_1/tree/PEC2), [PEC3](https://github.com/mdiazrioUOC/TFM_2025_1/tree/PEC3), and [PEC4](https://github.com/mdiazrioUOC/TFM_2025_1/tree/PEC4).

# Flask-based Web Application

This is a Flask-based web application to anotate clinical notes according to the Human Phenotype Ontology codification system. Below are the instructions on how to get started, run the app, and create a Docker image. This Readme file relates to the flask application to makes AI inferences against clinical notes. The code related to the web interface for annotating clinical notes can be found under the folder "clinical_annotator".

## Getting Started

### Prerequisites

- Python 3.8+
- Docker (optional but recommended)
- `pip` or `pipenv` for dependency management

### 1. Clone the GitHub Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/mdiazrioUOC/TFM_2025_1.git
cd TFM_2025_1
```

2. **Create an .env file at this location and add the following variables:**

```bash
VOYAGE_API_KEY="VOYAGE API KEY"
OPENAI_API_KEY="OPENAI API KEY"
PROJECT_DIR="The directory where the .env file is located"
CHROMADB_CONNECTION="The URL of the chroma DB"
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Start flask server**

```bash
cd src
python app.py
```

## Processing API

This application exposes an API that translates clinical text into HPO concepts.
This API:

1. Receives a POST request with a JSON payload

```json
{
  "text": "The patient shows signs of hepatomegaly and hypotonia."
}
```

2. Returns a structed JSON object containing

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

To run the app inside Docker:

```bash
docker build -t tfm20251:latest .
docker run --env-file .env -p 5000:5000 tfm20251:latest
```

## License

CC BY-NC License.
Author: Malena Díaz Río
