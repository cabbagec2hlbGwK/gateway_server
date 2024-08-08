import os
import random

import sys
import time
import boto3
import logging
import json
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger("manageQueue_task")

class SqsConsumer:
    def __init__(self, sqsUrl) -> None:
        self.sqsUrl = sqsUrl
        self.sqs = boto3.client('sqs')

    def process_message(self, message):
        print(f"Processing message: {message['Body']}")

    def consume_messages(self):
        try:
            while True:
                response = self.sqs.receive_message(
                    QueueUrl=self.sqsUrl,
                    AttributeNames=['All'],
                    MaxNumberOfMessages=10,
                    MessageAttributeNames=['All'],
                    VisibilityTimeout=10,  # Seconds
                    WaitTimeSeconds=2  # Long polling
                )

                messages = response.get('Messages', [])

                if not messages:
                    print("No messages to process. Waiting...")
                    time.sleep(10)
                    continue

                for message in messages:
                    try:
                        self.process_message(message)

                        self.sqs.delete_message(
                            QueueUrl=self.sqsUrl,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        log.info(f"Deleted message: {message['MessageId']}")

                    except Exception as e:
                        log.error(f"Error processing message: {e}")

        except (NoCredentialsError, PartialCredentialsError):
            log.error("Credentials not available")
        except Exception as e:
            log.error(f"Error: {e}")




class SqsProcucer :
    def __init__(self, sqsUrl) -> None:
        self.sqsUrl = sqsUrl
        self.sqs = boto3.client('sqs')

    def send_message(self, messageBody, messageAttributes=None):
        try:
            # Send message to SQS queue
            response = self.sqs.send_message(
                QueueUrl=self.sqsUrl,
                MessageBody=messageBody,
                MessageGroupId="group1",
                MessageAttributes=messageAttributes or {}
            )

            log.info(f'Message ID: {response["MessageId"]}')
            return response

        except (NoCredentialsError, PartialCredentialsError):
            log.error("Credentials not available")
        except Exception as e:
            log.error(f"Error: {e}")


def main():
    if len(sys.argv) <1:
        return 100
    print(sys.argv[1])
    if sys.argv[1] in "pro":
        url = os.getenv("SQSURL","https://sqs.us-east-1.amazonaws.com/536380612665/DCEMAIL.fifo")
        procucer = SqsProcucer(url)
        procucer.send_message(f"this is s test {random.randint(0,123218937)}")
        print("created")
    if sys.argv[1] in "con":
        url = os.getenv("SQSURL","https://sqs.us-east-1.amazonaws.com/536380612665/DCEMAIL.fifo")
        consumer = SqsConsumer(url)
        consumer.consume_messages()


       
if __name__=="__main__":
    main()
