import smtplib
import os
from utils.manageQueue import SqsConsumer

def sender(message, mailfrom, rcpttos):
    with smtplib.SMTP(host='smtp-relay.gmail.com', port=587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.send_message(message, mailfrom, rcpttos)
        smtp.quit()
    return '250 OK' ### ADDED RETURN


def main():
    url = os.getenv("SQSURL","https://sqs.us-east-1.amazonaws.com/536380612665/DCEMAIL.fifo")
    consumer = SqsConsumer(url)
    consumer.consume_messages()
    

