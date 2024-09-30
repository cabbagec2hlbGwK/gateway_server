import argparse
from flask import Flask, request, send_file, redirect, url_for
import requests
from botocore.exceptions import ClientError
import logging
import json
import re
import boto3
import argparse
import os
from piivalidator import PiiValidator

log = logging.getLogger("pii_dector_app")

PII_TYPES=[
        "email",
        "sin",
        "ssn",
        "account",
        "routing",
        "address",
        "phone",
        "passport",
        "address"
        ]

parser = argparse.ArgumentParser(description="Email reciver to handel reciving and QQ of the messages")
parser.add_argument("--host", required=True)
parser.add_argument("--api", required=True)
args = parser.parse_args()
apiEndpoint = args.api

def swap_dict(input_dict):
    output_dict = {}
    for key, values in input_dict.items():
        for value in values:
            output_dict[value] = key
    return output_dict

def cardCheck(card_number: str) -> bool:
    card_number = card_number.replace(" ", "")
    reversed_digits = [int(d) for d in card_number[::-1]]
    
    total = 0
    for i, digit in enumerate(reversed_digits):
        if i % 2 == 1:  
            doubled = digit * 2
            if doubled > 9:  
                total += (doubled - 9)  
            else:
                total += doubled
        else:
            total += digit
    return total % 10 == 0

def extractNumbers(text, num_chars):
    longNumbers = [re.sub(r'[^0-9]', '', i) for i in re.findall(r'\d+(?:[^\d\S-]*-?[^\d\S-]*\d+)*', text) if len( re.sub(r'[^0-9]', '', i))>= num_chars]
    results = []
    for number in longNumbers:
        for i in range(len(number) - num_chars + 1):
            results.append(number[i:i + num_chars])
    return results
def extract_card_info(text):
    card_patterns = {
        14: {
            'Diners Club Carte Blanche': r'^(300|301|302|303|304|305)[0-9]{11}$',
            'Diners Club International': r'^36[0-9]{12}$',
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
            'Visa': r'^4[0-9]{14}$',
        },
        15: {
            'American Express': r'^(34|37)[0-9]{13}$',
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
        },
        16: {
            'Diners Club US and Canada': r'^(54|55)[0-9]{14}$',
            'Discover Card': r'^(6011|622[1-9][0-9]{5}|64[4-9][0-9]{13}|65[0-9]{14})[0-9]{12}$',
            'InstaPayment': r'^(637|638|639)[0-9]{13}$',
            'JCB': r'^(352[8-9]|35[3-8][0-9])[0-9]{12}$',
            'Mastercard': r'^(5[1-5][0-9]{14}|2221[0-9]{12}|22[2-7][0-9]{13}|2720[0-9]{12})$',
            'Visa': r'^4[0-9]{15}$',
            'Visa Electron': r'^(4026[0-9]{12}|417500[0-9]{10}|4508[0-9]{12}|4844[0-9]{12}|4913[0-9]{12}|4917[0-9]{12})$',
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
        },
        19: {
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
            'Visa': r'^4[0-9]{18}$',
            'Discover Card': r'^(6011[0-9]{15}|622[12][0-9]{13}|622[3-8][0-9]{14}|6229[0-2][0-9]{13}|644[0-9]{15}|645[0-9]{15}|646[0-9]{15}|647[0-9]{15}|648[0-9]{15}|649[0-9]{15}|65[0-9]{17})$',
            'Laser': r'^(6304|6706|6771|6709)[0-9]{15,18}$', 
            'JCB': r'^(352[8-9]|35[3-8][0-9])[0-9]{12,15}$',
        },
    }

    matches = dict()

    for key, patterns in card_patterns.items():
        data = extractNumbers(text, key)
        print(len(data))
        if data == []:
            pass
            return swap_dict(matches)
        for card_number in data:
            for name, pattern in patterns.items():
                if re.fullmatch(pattern, card_number) and cardCheck(card_number):
                    mat = matches.get(name, list())
                    mat.append(card_number)
                    matches[name] = mat
    return swap_dict(matches)

class PiiDetector:
    def __init__(self, comprehend):
        self.model = comprehend
        KEY = os.getenv("azurelanguage")
        ENDPOINT = "https://digicontrolpiidetect.cognitiveservices.azure.com/language/:analyze-text?api-version=2022-05-01"
        validatpr = PiiValidator(KEY, ENDPOINT)
        self.azure = validatpr

    def detect_languages(self, text):
        try:
            log.debug(text)
            response = self.model.detect_dominant_language(Text=text)
            languages = response['Languages'][0]['LanguageCode']
            log.info("Detected %s languages.", len(languages))
        except ClientError:
            log.exception("Couldn't detect languages.")
            raise
        else:
            return "en"


    def detect_pii(self, text, language_code):
        try:
            response = self.model.detect_pii_entities(
                Text=text, LanguageCode=str(language_code)
            )
            entities = response["Entities"]
            log.info("Detected %s PII entities.", len(entities))
        except ClientError as e:
            print(e)
            log.exception("Couldn't detect PII entities.")
            raise
        else:
            return entities

    def azureScan(self, text):
        pii = self.azure.validate([text])
        piis = []
        return[]
        for p in pii:
            if p.get("confidenceScore") > 0.88:
                log.debug(p)
                piis.append(p)
        return piis

    def isSin(self, text):
        sin = text.replace(" ", "").replace("-", "")
        if len(sin)>=10:
            return "PHONE"

        if not sin.isdigit() or len(sin) != 9:
            return "Possible_pii"

        digits = [int(d) for d in sin]

        checksum = 0
        for i in range(9):
            if i % 2 == 0:
                checksum += digits[i]
            else: 
                doubled = digits[i] * 2
                checksum += doubled if doubled < 10 else doubled - 9
        if checksum % 10 ==0:
            return "Canadian_SIN"
        else:
            return "possible_SIN"

    def scan(self, data):
        found = self.detect_pii(data, self.detect_languages(data))
        piis = dict()
        for pii in found:
            if any(str(pii.get('Type')).lower() in str(regPii).lower() for regPii in PII_TYPES):
                value = data[pii.get("BeginOffset"):pii.get("EndOffset")]
                piis[value] = pii.get("Type")
                if "PHONE" in pii.get("Type"):
                    piis[value.replace(" ","").replace("-","")] = self.isSin(value)
                    if value != value.replace(" ","").replace("-",""):
                        del piis[value]
        log.debug(piis)
        sins = extractNumbers(data, 9)
        for sin in sins:
            if self.isSin(sin) in "Canadian_SIN":
                piis[sin]="Canadian_SIN"
        piis.update(extract_card_info(data))
        return json.dumps(piis)
            

app = Flask(__name__)


@app.route("/")
def root():
    return send_file('assets/index.html')

@app.route("/detect", methods=['POST'])
def detect():
    data = request.json
    res = detctor.scan(data.get("text"))
    return res
    

@app.route("/extract", methods=['POST'])
def extract():
    if 'test' not in request.files:
        return "No file part", 400
    
    file = request.files['test']
    if file.filename == '':
        return "No selected file", 400
    
    if file:
        files = {'test': (file.filename, file.stream, file.mimetype)}
        res = requests.post(url=f"http://{apiEndpoint}:8080/extract", files=files)
        log.debug(res.text)
        respii = detctor.scan(res.text)
        azure = detctor.azureScan(res.text)
        log.debug(azure)
        return str(respii)

if __name__ == "__main__":
    REGION = os.getenv("AWS_REGION","us-east-1")
    detctor = PiiDetector(boto3.client("comprehend", region_name=REGION))
    app.run(host=args.host)

