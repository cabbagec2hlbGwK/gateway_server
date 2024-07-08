from os.path import commonpath
from botocore import regions
from flask import Flask, request, send_file, redirect, url_for
import requests
import os, re
import crim as CommonRegex
from botocore.exceptions import ClientError
import logging
import boto3

logger = logging.getLogger(__name__)

class PiiDetector:
    def __init__(self, comprehend):
        self.model = comprehend

    def detect_languages(self, text):
        try:
            response = self.model.detect_dominant_language(Text=text)
            languages = response["Languages"]
            logger.info("Detected %s languages.", len(languages))
        except ClientError:
            logger.exception("Couldn't detect languages.")
            raise
        else:
            return languages


    def detect_pii(self, text, language_code):
        try:
            response = self.model.detect_pii_entities(
                Text=text, LanguageCode=language_code
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

def detect(data):
    pass

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
        res = requests.post(url="http://localhost:8080/extract", files=files)
        print(res.text)
        res = detctor.scan(res.text)
        return str(res)

if __name__ == "__main__":
    REGION = os.getenv("AWS_REGION","us-west-1")
    detctor = PiiDetector(boto3.client("comprehend", regions=REGION))
    app.run(debug=True, host="")

