import boto3
from werkzeug.datastructures import FileStorage
from pdf2image import convert_from_bytes
from PIL import Image
import io
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
        if "pdf" in file.content_type.split("/")[1]:
            print("extracting pdf")
            extracted_text = extract_pdf(file_content)
        else:
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


def extract_pdf(data):
    print("+"*100) 
    pages = convert_from_bytes(data)
    first_page = pages[0]
    text = ""
    for first_page in pages:
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)  # Move to the beginning of the BytesIO buffer
        data = FileStorage(stream=img_byte_arr, filename='image.png', content_type='image/png')
        text = text+ extract(data.read())
    return text



if __name__ == "__main__":
    app.run(debug=True, port=8080)

