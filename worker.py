import requests
import uuid
import logging
import base64
import os
import io
import pandas as pd
import argparse
import pypandoc
import json
import time
from email import message_from_bytes
from email.policy import default
from utils.manageS3 import S3Manage
from utils.manageQueue import SqsConsumer, SqsProcucer
log = logging.getLogger("worker_task")


#--------------------------
DLP_POLICY = json.load(open("pollicy.json","r"))
blacklist_sender, blacklist_receiver = DLP_POLICY['user']['blackList'].get('senderList', []), DLP_POLICY['user']['blackList'].get('receiverList', [])
whitelist_sender, whitelist_receiver = DLP_POLICY['user']['whiteList'].get('senderList', []), DLP_POLICY['user']['whiteList'].get('receiverList', [])
pii_not_present_default = DLP_POLICY['message']['messageType']['piiNotPresent'].get('default')
user_is_registered_default = DLP_POLICY['message']['userType']['userIsRegistered'].get('default')
user_not_registered_default = DLP_POLICY['message']['userType']['userNotRegistered'].get('default')
pii_list = DLP_POLICY.get('pii', [])

def isWhitelistUser(user):
    for email in whitelist_receiver + whitelist_sender:
        if user == email :
            return True
    return False

def isBlacklistUser(user):
    for email in blacklist_receiver + blacklist_sender:
        if user == email :
            return True
    return False

#--------------------------

def extract_docx(data):
    unique_docx_filename = f"temp_{uuid.uuid4()}.docx"
    unique_pdf_filename = f"temp_{uuid.uuid4()}.pdf"

    with open(unique_docx_filename, "wb") as temp_docx:
        temp_docx.write(data)

    pypandoc.convert_file(unique_docx_filename, 'pdf', outputfile=unique_pdf_filename)

    with open(unique_pdf_filename, "rb") as temp_pdf:
        pdf_bytes = temp_pdf.read()

    os.remove(unique_docx_filename)
    os.remove(unique_pdf_filename)

    return pdf_bytes


def extract_excel_to_csv(data):
    excel_buffer = io.BytesIO(data)
    df = pd.read_excel(excel_buffer)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    csv_text = csv_buffer.getvalue()
    return csv_text

def process(envelope, args, objKey):
    mailfrom = envelope.mail_from
    rcpttos = envelope.rcpt_tos
    message = message_from_bytes(envelope.content, policy=default)
    data = {"message":message, "rcpttos":rcpttos,"mailfrom":mailfrom}
    body = message.get_payload()
    emailMess = None
    attachments = list()
    if not isinstance(body, str) and len(body)>1:
        emailMess = body[0]
        attachments = body[1:]
    else:
        emailMess = body
    log.debug(f"Message: {emailMess}, Attachments: {len(attachments)}")

    text = ""
    keywords = ['png','jpeg','pdf']
    print(attachments)
    for attachment in attachments:
        metadata = attachment.get("Content-Type").split(";")
        print("------------------")
        if any(keyword in item.lower() for item in metadata for keyword in keywords):
            print("this is runnin  --------------------------*")
            contentType = metadata[0].strip()
            name = metadata[1].split("=")[1].replace('"','').strip()
            rawBits = base64.b64decode(attachment.get_payload())
            files =  {'test': (name, rawBits, contentType)}
            url = f"http://{args.api}:5000/extract"
            res = requests.post(url, files=files)
            log.debug(res.text)
            text += res.text
        if 'docx' in metadata[1] or 'dox' in metadata[1]:
            contentType = 'application/pdf'
            name = metadata[1].split("=")[1].replace('"','').strip().replace(".docx", ".pdf").replace(".dox",".pdf")
            rawBits = base64.b64decode(attachment.get_payload())
            rawBits = extract_docx(rawBits)
            files =  {'test': (name, rawBits, contentType)}
            url = f"http://{args.api}:5000/extract"
            res = requests.post(url, files=files)
            log.debug(res.text)
            text += res.text
            print(text)
        if 'xlsx' in metadata[1]:
            rawBits = base64.b64decode(attachment.get_payload())
            text += extract_excel_to_csv(rawBits)
        if 'text' in attachment:
            text += str(attachment) 
    url = f"http://{args.api}:5000/detect"
    res = requests.post(url, json={"text":text+str(emailMess)})
    piiFound = set()
    jres = json.loads(res.text.replace("'",'"'))

    for i in jres:
        piiFound.add(jres[i])
    if len(piiFound) ==0 or isWhitelistUser(mailfrom) or isWhitelistUser("".join(rcpttos)):
        url = os.getenv("SENDSQSURL","")
        procucer = SqsProcucer(url)
        procucer.send_message(json.dumps({"messageId":str(uuid.uuid4()),"s3Key":objKey, "time":str(time.time)}))
        print("created")
        return 0
    if isBlacklistUser(mailfrom) or isBlacklistUser("".join(rcpttos)):
        print("the message was proped as it was blacklisted")
        return 0
    else:
        url = os.getenv("OWNERIDENTY","")
        if not url:
            raise Exception("OWNERIDENTY not found")
        producer = SqsProcucer(url)
        #TODO need the work on the encription on it 
        producer.send_message(json.dumps({"messageId":str(uuid.uuid4()), "endUsers":json.dumps({"sender":mailfrom, "recivers":", ".join(rcpttos)}) ,"pii":json.dumps(jres), "s3Key":objKey,"timeStamp":time.time()}))
        return 1



def main():
    parser = argparse.ArgumentParser(description="worker handels the task of processing the information from the queue")
    parser.add_argument("--api", required=True) 
    args = parser.parse_args()

    key = os.getenv("ENCKEY", "t"*32).encode('utf-8')
    bucketName = os.getenv("S3BUCKET","testbbuckker12")
    url = os.getenv("SQSURL","https://sqs.us-east-1.amazonaws.com/536380612665/DCEMAIL.fifo")

    consumer = SqsConsumer(url)
    s3Manager = S3Manage(key, bucketName)


    #queueElement = {"id":str(uuid.uuid4()),"s3Key":ObjectKey,"from":mailfrom, "rcpttos":rcpttos,"timeStamp":str(datetime.now())} 
    #data = {"envelope":envelope,"mailfrom":mailfrom,"rcpttos":rcpttos}

    @consumer.process
    def handel_event(message):
        try:
            print(f"{type(message)}, {message}")
            objKey = message["s3Key"]
            print("WORKING....")
            data = s3Manager.s3Get(objKey)
            print("WORKING ")
            emailStatus = process(data.get("envelope"),args,objKey)
            print("WORKING ")
            if emailStatus != 0:
                print("Pii detected ---------------------")
        except Exception as e:
            print(e)


    consumer.consume_messages()


    

if "__main__"==__name__:
    main()
