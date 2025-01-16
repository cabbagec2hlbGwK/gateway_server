import smtplib
import os
from utils.manageQueue import SqsConsumer
from utils.manageS3 import S3Manage
from email import message_from_bytes
from email.policy import default

def sender(envelope):
    mailfrom = envelope.mail_from
    rcpttos = envelope.rcpt_tos
    message = message_from_bytes(envelope.content, policy=default)
    with smtplib.SMTP(host='smtp-relay.gmail.com', port=587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.send_message(message, mailfrom, rcpttos)
        smtp.quit()
    return '250 OK' ### ADDED RETURN


def main():
    url = os.getenv("SENDSQSURL","https://sqs.us-east-1.amazonaws.com/536380612665/DCEMAIL.fifo")
    key = os.getenv("ENCKEY", "t"*32).encode('utf-8')
    bucketName = os.getenv("S3BUCKET","testbbuckker12")

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
            sender(data.get("envelope"))
            return True
        except Exception as e:
            print(e)
            return False

    consumer.consume_messages()

main()

