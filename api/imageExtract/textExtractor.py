import boto3
from flask import Flask, request, jsonify

textract = boto3.client('textract')
app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extr():
    if 'test' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['test']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        file_content = file.read()
        extracted_text = extract(file_content)
        return jsonify({"text": extracted_text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract(data):
    response = textract.detect_document_text(
        Document={
            'Bytes': data
        }
    )

    extracted_lines = []
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            extracted_lines.append(item['Text'])

    return " ".join(extracted_lines)

if __name__ == "__main__":
    app.run(debug=True, port=8080)

