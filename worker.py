import requests
import uuid
import logging
import base64
import os
import argparse
import pypandoc
import json
import time
from email import message_from_bytes
from email.policy import default
from utils.manageS3 import S3Manage
from utils.manageQueue import SqsConsumer, SqsProcucer
log = logging.getLogger("worker_task")

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
    print(len(attachments))
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

        if 'text' in attachment:
            print(emailMess)
            text += str(attachment) 
    print(text)
    url = f"http://{args.api}:5000/detect"
    res = requests.post(url, json={"text":text+str(emailMess)})
    print(res.text)
    piiFound = set()
    jres = json.loads(res.text.replace("'",'"'))

    for i in jres:
        piiFound.add(jres[i])
    print(piiFound)
    if len(piiFound) ==0:
        url = os.getenv("SENDSQSURL","")
        procucer = SqsProcucer(url)
        procucer.send_message(json.dumps({"messageId":str(uuid.uuid4()),"s3Key":objKey, "time":str(time.time)}))
        print("created")
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
            data = s3Manager.s3Get(objKey)
            emailStatus = process(data.get("envelope"),args,objKey)
            if emailStatus != 0:
                print("Pii detected ---------------------")
        except Exception as e:
            print(e)


    consumer.consume_messages()


    

if "__main__"==__name__:
    main()
