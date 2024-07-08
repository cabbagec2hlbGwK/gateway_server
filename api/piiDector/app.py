import argparse
from flask import Flask, request, send_file, redirect, url_for
import requests
from botocore.exceptions import ClientError
import logging
import boto3
import argparse

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Email reciver to handel reciving and QQ of the messages")
parser.add_argument("--host", required=True)
args = parser.parse_args()


class PiiDetector:
    def __init__(self, comprehend):
        self.model = comprehend

    def detect_languages(self, text):
        try:
            print(text)
            response = self.model.detect_dominant_language(Text=text)
            languages = response['Languages'][0]['LanguageCode']
            logger.info("Detected %s languages.", len(languages))
        except ClientError:
            logger.exception("Couldn't detect languages.")
            raise
        else:
            return languages


    def detect_pii(self, text, language_code):
        try:
            response = self.model.detect_pii_entities(
                Text=text, LanguageCode=str(language_code)
            )
            entities = response["Entities"]
            logger.info("Detected %s PII entities.", len(entities))
        except ClientError:
            logger.exception("Couldn't detect PII entities.")
            raise
        else:
            return entities

    def scan(self, data):
        found = self.detect_pii(data, self.detect_languages(data))
        return found
            

app = Flask(__name__)


@app.route("/")
def root():
    return send_file('assets/index.html')

@app.route("/extract", methods=['POST'])
def extract():
    if 'test' not in request.files:
        return "No file part", 400
    
    file = request.files['test']
    if file.filename == '':
        return "No selected file", 400
    
    if file:
        files = {'test': (file.filename, file.stream, file.mimetype)}
        res = requests.post(url=f"http://{args.host}:8080/extract", files=files)
        print(res.text)
        res = detctor.scan(res.text)
        return str(res)

if __name__ == "__main__":
    REGION = os.getenv("AWS_REGION","us-east-1")
    detctor = PiiDetector(boto3.client("comprehend", region_name=REGION))
    app.run(debug=True, host=args.host)

