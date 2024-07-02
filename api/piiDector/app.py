from os.path import commonpath
from flask import Flask, request, send_file, redirect, url_for
import requests
import os, re
import crim as CommonRegex

class PiiDetector:
    def __init__(self):
        pass
    def getPii(self,data):
        found = dict()
        found["email"] = CommonRegex.emails(data)
        found["link"] = CommonRegex.links(data)
        found["visa"] = CommonRegex.visa_cards(data)
        found["master"] = CommonRegex.master_cards(data)
        found["credit"] = CommonRegex.credit_cards(data)
        found["address"] = CommonRegex.street_addresses(data)
        found["phone"] = CommonRegex.phones(data)
        found["ip4"] = CommonRegex.ipv4s(data)
        found["ip6"] = CommonRegex.ipv6s(data)
        found["snn"] = CommonRegex.ssn_numbers(data)
        return found


    def scan(self, data):
        detected = dict()
        found = self.getPii(data)
        for pii in found.keys():
            if len(found.get(pii)) >0:
                detected[pii] = found.get(pii)
        return detected
            

app = Flask(__name__)
detctor = PiiDetector()

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
        res = detctor.scan(res.text)
        return str(res)

if __name__ == "__main__":
    app.run(debug=True)

