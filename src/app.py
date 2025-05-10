import sys
import json
import dotenv
dotenv.load_dotenv()
from flask import Flask, request, jsonify
from utils.customchain import custom_chain

app = Flask(__name__)

# Call the chain
def process_clinical_note(clinical_note):
    answer = custom_chain.invoke({"clinical_note":clinical_note}, with_positions=True)
    answer = json.dumps(answer, default=vars)
    return answer

# Define the endpoint for POST requests
@app.route('/process_note', methods=['POST'])
def process_note():
    # Get the JSON data from the POST request
    data = request.get_json()

    # Check if the 'clinical_note' key is in the data
    if 'clinical_note' not in data:
        return jsonify({"error": "Clinical note not provided"}), 400

    # Extract the clinical note
    clinical_note = data['clinical_note']

    # Call the function to process the note
    result = process_clinical_note(clinical_note)

    # Return the result as a JSON response
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
