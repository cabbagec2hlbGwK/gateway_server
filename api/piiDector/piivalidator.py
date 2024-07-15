import uuid
import json
import requests
import os
class PiiValidator:
    def __init__(self, apiKey, endPoint) -> None:
        self.endPoints = endPoint
        self.key= apiKey


    def jsonfy(self, text):
        if not text:
            print("No text for passed for the resBody")
        jsonData = {
                "kind": "PiiEntityRecognition",
                "parameters": {
                    "modelVersion": "latest"
                },
                "analysisInput":{
                    "documents":[
                                {
                                "id":str(uuid.uuid4()),
                                "language": "en",
                                "text": " ".join(text)
                                }
                            ]
                }
            }
        return jsonData

    def requestPii(self, jsonData):
        headers = {
                "Content-Type":"application/json",
                "Ocp-Apim-Subscription-Key": self.key
                }
        try:
           return requests.post(url=self.endPoints,json=jsonData, headers=headers)
        except Exception as e:
            print(e)

#------------------------------------------------------------------------------
    def validate(self, text:list):
        try:
            jsonData = self.jsonfy(text)
            res = self.requestPii(jsonData)
            res = json.loads(res.text)
            return res['results']['documents'][0]['entities']
        except Exception as e:
            print(e)
            print("The test ran into some issues")

if __name__ == "__main__":
    KEY = os.getenv("azurelanguage")
    ENDPOINT = "https://digicontrolpiidetect.cognitiveservices.azure.com/language/:analyze-text?api-version=2022-05-01"
    validatpr = PiiValidator(KEY, ENDPOINT)
    pii = validatpr.validate(["""PASSPORT PASSEPORT
CANADA
Type/Type
Issuing Country/Pays émetteur
P
CAN
Passport No./N° de passeport
Surname/Nom MARTIN
ZE000509
MEN
Given names/Prénoms
SARAH
Nationality/Nationalité
CANADIAN/CANADIENNE
Date of birth/Date de naissance
01 JAN/JAN 85
Sex/Sexe Place of birth/Lieu de naissance
F
OTTAWA WA CAN
Date of issue/Date de délivrance
14 JANJAN 13
Date of expiry/Date d'expiration
14 JAN/JAN 23
Issuing Authority/Autorité de délivrance
GATINEAU
P<CANMARTIN<<SARAH<<<<<<<<<<<<<<<<<<<<<<<<<<
ZE000509<9CAN8501019F2301147<<<<<<<<<<<<<<08"""])
    for p in pii:
        if p.get("confidenceScore") > 0.88:
            print(p)


