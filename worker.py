import requests
import logging
import base64
import os
import argparse
import json
from email import message_from_bytes
from email.policy import default
from utils.manageS3 import S3Manage

from utils.manageQueue import SqsConsumer, SqsProcucer
log = logging.getLogger("worker_task")

def process(envelope, args):
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
    print(len(attachments))
    for attachment in attachments:
        print("--------------------------------------------------------")
        metadata = attachment.get("Content-Type").split(";")
        contentType = metadata[0].strip()
        name = metadata[1].split("=")[1].replace('"','').strip()
        rawBits = base64.b64decode(attachment.get_payload())
        files =  {'test': (name, rawBits, contentType)}
        url = f"http://{args.api}:5000/extract"
        res = requests.post(url, files=files)
        text += res.text
        print(res.text)
        log.debug(res.text)
    print(text)
    url = f"http://{args.api}:5000/detect"
    res = requests.post(url, json={"text":text+str(emailMess)})
    print(res.text)
    piiFound = set()
    jres = json.loads(res.text.replace("'",'"'))

    for i in jres:
        piiFound.add(jres[i])
    print(piiFound)
    url = os.getenv("SENDSQSURL","https://sqs.us-east-1.amazonaws.com/536380612665/scaned.fifo")
    procucer = SqsProcucer(url)
    procucer.send_message(json.dumps({"pii":" ".join(piiFound)}))
    print("created")


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
        print(f"{type(message)}, {message}")
        objKey = message["s3Key"]
        data = s3Manager.s3Get(objKey)
        process(data.get("envelope"),args)

    consumer.consume_messages()


    

if "__main__"==__name__:
    main()
