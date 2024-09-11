import json
import os
import argparse
import requests
from utils.manageQueue import SqsConsumer
from utils.manageQueue import SqsProcucer

def getUser(piiInformation, endpoint):
    endpoint = endpoint
    user = requests.post(url=endpoint, json=piiInformation)
    userJson = json.loads(user.content)
    return userJson.get('user')


def main():
    parser = argparse.ArgumentParser(description="worker handels the task of processing the information from the queue and associate a user to it")
    parser.add_argument("--identity_endpoint", required=True) 
    args = parser.parse_args()
    piiQueue = os.getenv("OWNERIDENTY","https://sqs.us-east-2.amazonaws.com/767397688321/OwnerIdentification.fifo")
    pendinfApproval = os.getenv("APPROVALSQSURL","https://sqs.us-east-2.amazonaws.com/767397688321/approval_list.fifo")

    consumer = SqsConsumer(piiQueue)
    producer = SqsProcucer(pendinfApproval)

        #producer.send_message(json.dumps({"messageId":str(uuid.uuid4()),"pii":json.dumps(jres), "s3Key":objKey,"timeStamp":time.time()}))
    @consumer.process
    def handel_event(message):
        try:
            messaageID = message["messageId"]
            s3Key = message["s3Key"]
            piiFound = json.loads(message["pii"])
            timeStamp = message["timeStamp"]
            user = getUser(piiFound, args.identity_endpoint)
            producer.send_message(json.dumps({"messageId":messaageID, "s3Key": s3Key, "pii":piiFound,"user":user, "timeStamp":timeStamp}))

        except Exception as e:
            print(e)


    consumer.consume_messages()


if __name__=="__main__":
    main()
