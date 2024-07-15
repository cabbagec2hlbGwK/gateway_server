import argparse
from flask import Flask, request, send_file, redirect, url_for
import requests
from botocore.exceptions import ClientError
import logging
import boto3
import argparse
import os
from piivalidator import PiiValidator

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Email reciver to handel reciving and QQ of the messages")
parser.add_argument("--host", required=True)
args = parser.parse_args()


class PiiDetector:
    def __init__(self, comprehend):
        self.model = comprehend
        KEY = os.getenv("azurelanguage")
        ENDPOINT = "https://digicontrolpiidetect.cognitiveservices.azure.com/language/:analyze-text?api-version=2022-05-01"
        validatpr = PiiValidator(KEY, ENDPOINT)
        self.azure = validatpr

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
            return "en"


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

    def azureScan(self, text):
        pii = self.azure.validate([text])
        piis = []
        for p in pii:
            if p.get("confidenceScore") > 0.88:
                print(p)
                piis.append(p)
        return piis

    def isSin(self, text):
        sin = text.replace(" ", "").replace("-", "")
        if len(sin)>=10:
            return "PHONE"

        if not sin.isdigit() or len(sin) != 9:
            return "PHONE"

        digits = [int(d) for d in sin]

        checksum = 0
        for i in range(9):
            if i % 2 == 0:
                checksum += digits[i]
            else: 
                doubled = digits[i] * 2
                checksum += doubled if doubled < 10 else doubled - 9
        if checksum % 10 ==0:
            return "Canadian SIN"
        else:
            return "PHONE"

    def scan(self, data):
        found = self.detect_pii(data, self.detect_languages(data))
        piis = dict()
        for pii in found:
            value = data[pii.get("BeginOffset"):pii.get("EndOffset")]
            piis[value] = pii.get("Type")
            if "PHONE" in pii.get("Type"):
                piis[value] = self.isSin(value)
        print(piis)
        return piis
            

app = Flask(__name__)


@app.route("/")
def root():
    return send_file('assets/index.html')

@app.route("/detect", methods=['POST'])
def detect():
    data = request.json
    res = detctor.scan(data.get("text"))
    return str(res)
    

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
        respii = detctor.scan(res.text)
        azure = detctor.azureScan(res.text)
        print(azure)
        return str(respii)

if __name__ == "__main__":
    REGION = os.getenv("AWS_REGION","us-east-1")
    detctor = PiiDetector(boto3.client("comprehend", region_name=REGION))
    app.run(debug=True, host=args.host)

