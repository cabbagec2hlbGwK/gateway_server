import requests
import logging
import base64
import os
import argparse
import smtplib
from email import message_from_bytes
from email.policy import default
from utils.manageS3 import S3Manage

from utils.manageQueue import SqsConsumer
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
    url = f"http://{args.api}:5000/detect"
    res = requests.post(url, json={"text":str(emailMess)})
    log.debug(res.text)

    for attachment in attachments:
        metadata = attachment.get("Content-Type").split(";")
        contentType = metadata[0].strip()
        name = metadata[1].split("=")[1].replace('"','').strip()
        files =  {'test': (name, base64.b64decode(attachment.get_payload()), contentType)}
        url = f"http://{args.api}:5000/extract"
        res = requests.post(url, files=files)
        log.debug(res.text)

    with smtplib.SMTP(host='smtp-relay.gmail.com', port=587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.send_message(message, mailfrom, rcpttos)
        smtp.quit()

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
        

    consumer.consume_messages()


    

if "__main__"==__name__:
    main()
